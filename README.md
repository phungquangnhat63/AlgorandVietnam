# GoAndMint - NFT Event Ticket System on Algorand

GoAndMint is a Go-based application that enables event organizers to create and distribute NFT tickets on the Algorand blockchain. This project was developed as part of the Algorand Hackathon to demonstrate the potential of NFTs as digital event tickets.

## Features

- Create NFT tickets with detailed event metadata
- Store ticket information on the Algorand blockchain
- Transfer NFT tickets to event attendees
- Support for customizable event details
- Automated metadata generation
- Built on Algorand's secure and efficient blockchain

## Prerequisites

Before running this application, make sure you have the following installed:
- Go 1.17 or later
- Algorand account with sufficient ALGO tokens
- Access to Algorand node (testnet or mainnet)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/goandmint.git
cd goandmint
```

2. Install dependencies:
```bash
go mod init goandmint
go get github.com/algorand/go-algorand-sdk
```

3. Configure your environment:
```bash
# Create a .env file (optional)
touch .env
# Add your Algorand node details and credentials
```

## Configuration

Update the following constants in `main.go`:

```go
const (
    algodAddress = "https://testnet-api.algonode.cloud"  // Your Algorand node URL
    algodToken   = ""                                    // Your API token
)
```

## Usage

1. Create an event NFT:
```bash
go run main.go
```

2. Monitor the created NFT:
- Check the transaction ID in the console output
- View the asset on Algorand Explorer

3. Transfer NFT tickets:
```go
// Example code to transfer an NFT ticket
err = transferNFT(client, assetID, creatorAccount, "RECEIVER_ADDRESS")
```

## Project Structure

```
goandmint/
├── main.go              # Main application code
├── README.md           # Project documentation
├── go.mod              # Go module file
└── go.sum              # Go dependencies checksum
```

## Smart Contract Details

The NFT tickets are created using Algorand Standard Assets (ASA) with the following properties:
- Total supply: 1 (making it a true NFT)
- Decimals: 0
- Default frozen: false
- URL: Points to metadata storage
- Metadata: Contains event details and ticket information

## Example Event Metadata

```json
{
    "event": {
        "name": "Algorand Hackathon 2024",
        "description": "Join us for an exciting hackathon event!",
        "location": "Virtual Event",
        "date": "2024-04-20",
        "ticketType": "General Admission"
    },
    "ticketId": "TICKET-001",
    "userAddress": "USER-WALLET-ADDRESS"
}
```

## Common Issues and Solutions

1. **Insufficient ALGO Balance**
   - Ensure your creator account has sufficient ALGO tokens
   - Use Algorand faucet for testnet tokens

2. **Transaction Failed**
   - Check network connection
   - Verify account has opted-in to receive ASA
   - Confirm correct addresses are being used

3. **Metadata Issues**
   - Verify JSON format is correct
   - Ensure metadata URL is accessible
   - Check character length limits

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security Considerations

- Keep private keys secure and never commit them to the repository
- Use environment variables for sensitive information
- Implement proper access controls for NFT transfers
- Validate all input data before creating NFTs

## License

This project is licensed under the MIT License - see the LICENSE file for details.


## Acknowledgments

- Algorand Foundation
- Go Algorand SDK Team
- Algorand Developer Community

---
Made with ❤️ for the Algorand Hackathon
