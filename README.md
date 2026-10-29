# cool62coin Wallet

## About

The cool62coin Wallet (cool62coingui) is the official wallet for [cool62coin](https://github.com/thecoolguy62aws/cool62coin), a decentralized proof-of-work cryptocurrency.

## Features

The cool62coin Wallet is much more user friendly and feature rich than the lightweight wallet included with [cool62coin](https://github.com/thecoolguy62aws/cool62coin). The biggest addition from the legacy CLI wallet is the ability to manage multiple accounts.

## Setup

### Windows/NT

1. Clone the repo onto your machine. The directory you put it in will be the installation directory.
2. Run `install.bat`.
3. Search for `cool62coin Wallet` in your operating system search menu. You will find it, and from there you can pin it to your taskbar, start menu, or make a desktop shortcut.

### Linux, Darwin, and other Unix-like kernals

Unfortunately, I haven't implemented install scripts for these operating systems yet, but I will very soon.

## Usage

When you open the app for the first time, you will see a banner greeting you and prompting to to create an account. Once you do this, you will be able to see your balance and make transactions and transfers.

**Highly Recommended**: For increased privacy, you should go to the `Node` page and switch it to `Background Local Node`. When you close the app, the node will automatically stop, and when you open it, it will automatically start again. Note that while the node is syncing with the network your balances may appear incorrect for a while (about 5 minutes). Make sure to periodically hit `Reload` to check if your balances are updated!