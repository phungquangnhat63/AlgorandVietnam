from pyteal import *
import json
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)

# Smart Contract cho Event và NFT
def approval_program():
    # Global state - thông tin sự kiện
    event_name = Bytes("name")
    event_description = Bytes("desc")
    event_date = Bytes("date")
    max_tickets = Bytes("max_tickets")
    tickets_sold = Bytes("tickets_sold")
    ticket_price = Bytes("price")
    event_creator = Bytes("creator")
    nft_asset_id = Bytes("nft_id")

    # Operations
    op_create_event = Bytes("create")
    op_buy_ticket = Bytes("buy")
    op_update_event = Bytes("update")

    @Subroutine(TealType.none)
    def create_event(name: Expr, description: Expr, date: Expr, max_tix: Expr, price: Expr):
        return Seq([
            App.globalPut(event_name, name),
            App.globalPut(event_description, description),
            App.globalPut(event_date, date),
            App.globalPut(max_tickets, max_tix),
            App.globalPut(tickets_sold, Int(0)),
            App.globalPut(ticket_price, price),
            App.globalPut(event_creator, Txn.sender()),
        ])

    @Subroutine(TealType.uint64)
    def buy_ticket(payment_amount: Expr):
        return Seq([
            Assert(payment_amount >= App.globalGet(ticket_price)),
            Assert(App.globalGet(tickets_sold) < App.globalGet(max_tickets)),
            App.globalPut(tickets_sold, App.globalGet(tickets_sold) + Int(1)),
            Int(1)
        ])

    program = Cond(
        [Txn.application_id() == Int(0),
         Seq([
             Assert(Txn.application_args.length() == Int(6)),
             create_event(
                 Txn.application_args[1],
                 Txn.application_args[2],
                 Btoi(Txn.application_args[3]),
                 Btoi(Txn.application_args[4]),
                 Btoi(Txn.application_args[5])
             ),
             Return(Int(1))
         ])],
        [Txn.application_args[0] == op_buy_ticket,
         Return(buy_ticket(Txn.amount()))],
    )

    return program

def clear_state_program():
    return Int(1)

# Helper functions để tương tác với smart contract
class GoAndMint:
    def __init__(self, algod_client):
        self.client = algod_client

    def compile_program(self, source_code):
        compile_response = self.client.compile(source_code)
        return base64.b64decode(compile_response['result'])

    def create_event_app(self, creator_private_key, name, description, date, max_tickets, price):
        # Compile approval program
        approval_program_source = compileTeal(
            approval_program(), mode=Mode.Application, version=6
        )
        approval_program_compiled = self.compile_program(approval_program_source)

        # Compile clear state program
        clear_state_source = compileTeal(
            clear_state_program(), mode=Mode.Application, version=6
        )
        clear_state_compiled = self.compile_program(clear_state_source)

        # Get creator account
        creator_account = account.address_from_private_key(creator_private_key)

        # Create transaction
        params = self.client.suggested_params()
        txn = transaction.ApplicationCreateTxn(
            sender=creator_account,
            sp=params,
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval_program_compiled,
            clear_program=clear_state_compiled,
            global_schema=transaction.StateSchema(num_uints=4, num_byte_slices=4),
            local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
            app_args=[b"create", 
                     name.encode(), 
                     description.encode(), 
                     date.to_bytes(8, 'big'),
                     max_tickets.to_bytes(8, 'big'),
                     price.to_bytes(8, 'big')]
        )

        # Sign and send transaction
        signed_txn = txn.sign(creator_private_key)
        tx_id = self.client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.client, tx_id, 4)
        app_id = result["application-index"]
        return app_id

    def create_nft_ticket(self, creator_private_key, app_id, metadata_url):
        creator_account = account.address_from_private_key(creator_private_key)
        params = self.client.suggested_params()

        # Create NFT
        txn = transaction.AssetConfigTxn(
            sender=creator_account,
            sp=params,
            total=1,
            default_frozen=False,
            unit_name="TICKET",
            asset_name=f"EventTicket#{app_id}",
            manager=creator_account,
            reserve=creator_account,
            freeze=creator_account,
            clawback=creator_account,
            url=metadata_url,
            decimals=0
        )

        # Sign and send transaction
        signed_txn = txn.sign(creator_private_key)
        tx_id = self.client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.client, tx_id, 4)
        asset_id = result["asset-index"]
        return asset_id

    def buy_ticket(self, buyer_private_key, app_id, ticket_price):
        buyer_account = account.address_from_private_key(buyer_private_key)
        params = self.client.suggested_params()

        # Create application call transaction
        app_call_txn = transaction.ApplicationCallTxn(
            sender=buyer_account,
            sp=params,
            index=app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"buy"],
            accounts=None,
            foreign_apps=None,
            foreign_assets=None,
        )

        # Create payment transaction
        payment_txn = transaction.PaymentTxn(
            sender=buyer_account,
            sp=params,
            receiver=self.get_app_address(app_id),
            amt=ticket_price
        )

        # Group transactions
        transaction.assign_group_id([app_call_txn, payment_txn])

        # Sign transactions
        signed_app_call = app_call_txn.sign(buyer_private_key)
        signed_payment = payment_txn.sign(buyer_private_key)

        # Send transactions
        tx_id = self.client.send_transactions([signed_app_call, signed_payment])
        result = transaction.wait_for_confirmation(self.client, tx_id, 4)
        return result

    def get_app_address(self, app_id):
        return logic.get_application_address(app_id)

# Example usage
def main():
    # Initialize Algorand client
    algod_token = "your-api-token"
    algod_address = "https://testnet-algorand.api.purestake.io/ps2"
    headers = {
        "X-API-Key": algod_token,
    }
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    # Initialize GoAndMint
    gam = GoAndMint(algod_client)

    # Create creator account
    creator_private_key, creator_address = account.generate_account()
    print(f"Creator address: {creator_address}")

    # Create event
    app_id = gam.create_event_app(
        creator_private_key,
        "Algorand Hackathon",
        "Join us for an amazing hackathon!",
        int(time.time()) + 86400,  # Event tomorrow
        100,  # Max tickets
        1000000  # Price in microAlgos (1 ALGO)
    )
    print(f"Created event with app ID: {app_id}")

    # Create NFT ticket template
    metadata_url = "https://your-metadata-url.com/ticket.json"
    asset_id = gam.create_nft_ticket(creator_private_key, app_id, metadata_url)
    print(f"Created NFT ticket template with asset ID: {asset_id}")

    # Example: Buy ticket
    buyer_private_key, buyer_address = account.generate_account()
    result = gam.buy_ticket(buyer_private_key, app_id, 1000000)
    print(f"Ticket purchased: {result}")

if __name__ == "__main__":
    main()
