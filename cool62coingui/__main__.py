import webview
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import threading
import sys
import os
import json
import requests
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import subprocess
import psutil

from . import core

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
ICON_DIR = BASE_DIR / "icon.ico"
CONFIG_DIR = BASE_DIR / "wallet.json"
KEYS_DIR = BASE_DIR / "keys"
PEERS_DIR = BASE_DIR / "peers.txt"

node_process = None
config = {}

app = FastAPI()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def _node(base, path, method="GET", body=None):
    try:
        resp = requests.request(method, base.rstrip("/") + path, json=body, timeout=30)
    except requests.RequestException as e:
        sys.stderr.write(f"error: cannot reach node ({e})\n")
        sys.exit(1)
    if resp.status_code >= 400:
        data = resp.json() if resp.headers.get("content-type") == "application/json" else {}
        sys.stderr.write(f"error: {resp.status_code} {data.get('error', resp.text)}\n")
        sys.exit(1)
    return resp.json()

def _kill_process_by_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.net_connections()
            for conn in connections:
                if conn.laddr.port == port:
                    proc.kill()
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    addresses = []
    accounts = []
    
    accounts_list = config.get("accounts", [])
    
    for account in accounts_list:
        addresses.append(core.address_from_public_key(serialization.load_pem_public_key(account[1].encode("utf-8"))))
        accounts.append(account[2])
        
    return templates.TemplateResponse(
        request,
        name="index.html",
        context={"accounts": accounts, "addresses": addresses}
    )

@app.get("/receive", response_class=HTMLResponse)
async def read_receive_page(request: Request):
    addresses = []
    accounts = []
    for account in config["accounts"]:
        addresses.append(core.address_from_public_key(serialization.load_pem_public_key(account[1].encode("utf-8"))))
        accounts.append(account[2])
    return templates.TemplateResponse(
        request,
        name="receive.html",
        context={"accounts": accounts, "addresses": addresses}
    )

@app.get("/send", response_class=HTMLResponse)
async def read_send_page(request: Request):
    addresses = []
    accounts = []
    for account in config["accounts"]:
        addresses.append(core.address_from_public_key(serialization.load_pem_public_key(account[1].encode("utf-8"))))
        accounts.append(account[2])
    return templates.TemplateResponse(
        request,
        name="send.html",
        context={"accounts": accounts, "addresses": addresses}
    )

@app.get("/transfer", response_class=HTMLResponse)
async def read_transfer_page(request: Request):
    addresses = []
    accounts = []
    for account in config["accounts"]:
        addresses.append(core.address_from_public_key(serialization.load_pem_public_key(account[1].encode("utf-8"))))
        accounts.append(account[2])
    return templates.TemplateResponse(
        request,
        name="transfer.html",
        context={"accounts": accounts, "addresses": addresses}
    )

@app.get("/history", response_class=HTMLResponse)
async def read_history_page(request: Request):
    addresses = []
    accounts = []
    for account in config["accounts"]:
        addresses.append(core.address_from_public_key(serialization.load_pem_public_key(account[1].encode("utf-8"))))
        accounts.append(account[2])
    return templates.TemplateResponse(
        request,
        name="history.html",
        context={"accounts": accounts, "addresses": addresses}
    )

@app.get("/node", response_class=HTMLResponse)
async def read_node_settings_page(request: Request):
    current_node = config.get("node", "https://coinnode.cool62.net")
    return templates.TemplateResponse(
        request,
        name="node.html",
        context={"current_node": current_node}
    )

class Api:
    def create_account(self, name):
        try:
            from mnemonic import Mnemonic
            mnemo = Mnemonic("english")
            
            seed_phrase = mnemo.generate(strength=256)
            
            entropy_bytes = mnemo.to_entropy(seed_phrase)
            priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(entropy_bytes))
            pub_key = priv_key.public_key()

            priv_pem = priv_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")

            pub_pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode("utf-8")

            config["accounts"].append([priv_pem, pub_pem, name or "Unnamed Account"])
            with open(str(CONFIG_DIR), "w") as f:
                json.dump(config, f, indent=4)
                
            return {"success": True, "seed_phrase": seed_phrase}
        except Exception as e:
            sys.stderr.write(f"Failed creating account: {e}\n")
            raise Exception(str(e))

    def import_account(self, name, seed_phrase):
        try:
            from mnemonic import Mnemonic
            mnemo = Mnemonic("english")
            
            clean_phrase = " ".join(seed_phrase.strip().split())
            
            if not mnemo.check(clean_phrase):
                raise Exception("The provided seed phrase is invalid or has a typo.")

            entropy_bytes = mnemo.to_entropy(clean_phrase)
            
            priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(entropy_bytes))
            pub_key = priv_key.public_key()
            
            pub_pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode("utf-8")
            
            matching_accounts = next((account for account in config["accounts"] if account[1] == pub_pem), None)
            if matching_accounts:
                raise Exception(f"This account is already saved in your wallet.")

            priv_pem = priv_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")

            config["accounts"].append([priv_pem, pub_pem, name or "Imported Account"])
            with open(str(CONFIG_DIR), "w") as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            sys.stderr.write(f"Seed import failed: {e}\n")
            raise Exception(str(e))


    def rename_account(self, index, new_name):
        try:
            idx = int(index)
            if idx < 0 or idx >= len(config["accounts"]):
                raise Exception("Target account index out of bounds.")
            
            config["accounts"][idx][2] = new_name or "Unnamed Account"

            with open(str(CONFIG_DIR), "w") as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            sys.stderr.write(f"Account rename failed: {e}\n")
            raise Exception(str(e))

    def delete_account(self, index):
        try:
            idx = int(index)
            if idx < 0 or idx >= len(config["accounts"]):
                raise Exception("Target account index out of bounds.")

            target_account = config["accounts"][idx]
            pub_key = serialization.load_pem_public_key(target_account[1].encode("utf-8"))
            address = core.address_from_public_key(pub_key)

            node_data = _node(config["node"], f"/balance?address={address}")
            current_balance = float(node_data["balance"])

            if current_balance > 0:
                raise Exception(f"Cannot delete account. Contains a remaining balance of {current_balance} C62.")

            config["accounts"].pop(idx)

            with open(str(CONFIG_DIR), "w") as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            sys.stderr.write(f"Account deletion pipeline rejected: {e}\n")
            raise Exception(str(e))

    def save_account_order(self, order_list):
        try:
            reordered_accounts = []
            for position in order_list:
                reordered_accounts.append(config["accounts"][int(position)])

            config["accounts"] = reordered_accounts

            with open(str(CONFIG_DIR), "w") as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            sys.stderr.write(f"Failed saving restructured ordering index data: {e}\n")
            raise Exception(str(e))
    
    def balance(self, address):
        try:
            node_data = _node(config["node"], f"/balance?address={address}")
            raw_balance = node_data["balance"]
            
            if isinstance(raw_balance, float) and raw_balance.is_integer():
                return int(raw_balance)
            return raw_balance
        except Exception as e:
            sys.stderr.write(f"Error fetching balance for {address}: {e}\n")
            return "Error"

    def send_transaction(self, from_address, to_address, amount, memo=None):
        try:
            try:
                amt_float = float(amount)
            except ValueError:
                raise Exception(f"Invalid amount format: '{amount}'")
                
            if amt_float < 0:
                raise Exception("Transaction amount must be non-negative")
                
            if not core.is_valid_address(to_address):
                raise Exception("Recipient address is not a valid cool62coin address structure.")

            node_data = _node(config["node"], f"/balance?address={from_address}")
            current_balance = float(node_data["balance"])
            if current_balance < (amt_float + 1.0):
                raise Exception(f"Insufficient funds. You need at least {amt_float + 1.0} C62 (includes 1 C62 network fee) but only have {current_balance} C62.")

            target_account = None
            for account in config["accounts"]:
                pub_key = serialization.load_pem_public_key(account[1].encode("utf-8"))
                derived_addr = core.address_from_public_key(pub_key)
                if derived_addr == from_address:
                    target_account = account
                    break
            
            if not target_account:
                raise Exception("The key context for selected account address was not found in wallet.json.")

            priv_key_pem_string = target_account[0]
            private_key = serialization.load_pem_private_key(
                priv_key_pem_string.encode("utf-8"),
                password=None
            )
            
            memo_str = memo.strip() if memo and memo.strip() else None

            nonce = int(time.time())
            signature = core.sign_transaction(private_key, from_address, to_address, amt_float, nonce, memo_str)

            tx_payload = {
                "sender": from_address,
                "receiver": to_address,
                "amount": amt_float,
                "nonce": nonce,
                "signature": signature
            }
            
            if memo_str:
                tx_payload["memo"] = memo_str

            node_response = _node(config["node"], "/transaction", method="POST", body=tx_payload)
            return node_response

        except Exception as e:
            sys.stderr.write(f"Wallet transaction payload pipeline error: {e}\n")
            raise Exception(str(e))

    def validate_address(self, address):
        try:
            return core.is_valid_address(address)
        except Exception:
            return False
    
    def get_history(self, address):
        try:
            tx_history = []
            seen_transactions = set()

            try:
                pool_data = _node(config["node"], "/txpool")
                pool_txs = pool_data.get("transactions", pool_data.get("txpool", []))
                for tx in pool_txs:
                    if tx.get("sender") == address or tx.get("receiver") == address:
                        tx_key = (tx.get("sender"), tx.get("receiver"), tx.get("nonce"), float(tx.get("amount", 0)))
                        
                        if tx_key not in seen_transactions:
                            seen_transactions.add(tx_key)
                            tx_history.append({
                                "sender": tx.get("sender"),
                                "receiver": tx.get("receiver"),
                                "amount": tx.get("amount"),
                                "nonce": tx.get("nonce"),
                                "memo": tx.get("memo", ""),
                                "signature": tx.get("signature"),
                                "status": "Unconfirmed"
                            })
            except Exception as pool_err:
                sys.stderr.write(f"Could not read txpool: {pool_err}\n")

            try:
                chain_data = _node(config["node"], "/chain")
                blocks = chain_data.get("blocks", chain_data.get("chain", []))
                
                for block in blocks:
                    block_height = block.get("height")
                    if block_height is None:
                        block_height = block.get("index")
                    if block_height is None:
                        block_height = "?"
                        
                    for tx in block.get("transactions", []):
                        if tx.get("sender") == address or tx.get("receiver") == address:
                            tx_key = (tx.get("sender"), tx.get("receiver"), tx.get("nonce"), float(tx.get("amount", 0)))
                            
                            if tx_key in seen_transactions:
                                for existing_tx in tx_history:
                                    if (existing_tx["sender"] == tx.get("sender") and 
                                        existing_tx["receiver"] == tx.get("receiver") and 
                                        existing_tx["nonce"] == tx.get("nonce") and 
                                        "?" in str(existing_tx["status"])):
                                        existing_tx["status"] = f"Mined (Block {block_height})"
                                continue

                            seen_transactions.add(tx_key)
                            tx_history.append({
                                "sender": tx.get("sender"),
                                "receiver": tx.get("receiver"),
                                "amount": tx.get("amount"),
                                "nonce": tx.get("nonce"),
                                "memo": tx.get("memo", ""),
                                "signature": tx.get("signature"),
                                "status": f"Mined (Block {block_height})"
                            })
            except Exception as chain_err:
                sys.stderr.write(f"Could not read chain history: {chain_err}\n")

            tx_history.sort(key=lambda x: x.get("nonce", 0), reverse=True)
            return tx_history

        except Exception as e:
            sys.stderr.write(f"Error compiling transaction history: {e}\n")
            return []
        
    def get_current_node(self):
        return config.get("node", "https://coinnode.cool62.net")

    def kill_local_node(self):
        global node_process
        if node_process and node_process.poll() is None:
            try:
                node_process.terminate()
                node_process.wait(timeout=1.0)
            except Exception:
                pass
            node_process = None
        
        _kill_process_by_port(9050)

        if sys.platform == "win32":
            try:
                import subprocess
                cmd = 'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8090 ^| findstr LISTENING\') do taskkill /f /pid %a'
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                sys.stderr.write(f"Taskkill port cleanup notice: {e}\n")
        else:
            try:
                import subprocess
                subprocess.run(["pkill", "-f", "node.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def switch_node(self, node_type, custom_url=None):
        global node_process
        try:
            target_url = "https://coinnode.cool62.net"
            
            if node_type == "local":
                target_url = "http://127.0.0.1:8090"
                
                if node_process is None or node_process.poll() is not None:
                    python_exe = sys.executable
                    node_script_path = BASE_DIR / "node.py"
                    
                    if not node_script_path.is_file():
                        raise Exception(f"Node not found")

                    log_file_path = BASE_DIR / "node.log"
                    log_file = open(log_file_path, "w", encoding="utf-8")
                    
                    _kill_process_by_port(9050)
                    
                    node_process = subprocess.Popen(
                        [python_exe, "node.py", "--port", "8090"], 
                        cwd=str(BASE_DIR),
                        env=os.environ.copy(),
                        stdout=log_file,  
                        stderr=log_file,  
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    time.sleep(3.0)
                    
            elif node_type == "remote":
                self.kill_local_node()
                target_url = "https://coinnode.cool62.net"
                
            elif node_type == "custom" and custom_url:
                self.kill_local_node()
                target_url = custom_url.strip()

            config["node"] = target_url
            with open(str(CONFIG_DIR), "w") as f:
                json.dump(config, f, indent=4)
                
            return {"success": True, "active_node": target_url}
        except Exception as e:
            sys.stderr.write(f"Failed switching node configuration: {e}\n")
            raise Exception(str(e))

    def close_window(self):
        self.kill_local_node()
        webview.windows[0].destroy()
        sys.exit(0)


local_node_started = False

def start_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")

def main():
    global config
    if sys.platform == 'win32':
        import ctypes
        appid = 'thecoolguy62aws.cool62coin.cool62coingui.0.0.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    
    if not PEERS_DIR.is_file():
        with open(str(PEERS_DIR), 'w') as f:
            f.write("""rh2jbsr5mad76pfh5dhoxy7hxfpvjf55zpcstmfxhctcciwzhj2uc2yd.onion
7gmhrcj6agxizusdua6pceus3izrbcqb2dkloow2c3vzo5adqqruxcad.onion
dkaabl6kn2talyhrri4vcppwavir4vwt6w2thytnwdcxz42p2p6ng3ad.onion
ojcbuwipqqthu5tr6vvk7ms2zhih22ykxia2galv7d3fh7m6lvq7j7ad.onion
pqhkg7fxgv7wkllx23ni7dpjqtct4sis67t5wjezav4pirqbm5u4yvqd.onion
m7riwrjpt4jw5uqjsf2tb36fvilous6f43enthnjh2w4dnq3wb2xcjqd.onion""")
    
    if not CONFIG_DIR.is_file():
        config = {"node": "https://coinnode.cool62.net", "accounts": []}
        with open(str(CONFIG_DIR), 'w') as f:
            json.dump(config, f, indent=4)
    else:
        with open(str(CONFIG_DIR), 'r') as f:
            try:
                config = json.load(f)
            except Exception:
                config = {"node": "https://coinnode.cool62.net", "accounts": []}

    if config.get("node") == "http://127.0.0.1:8090":
        global node_process
        python_exe = sys.executable
        node_script_path = BASE_DIR / "node.py"
        
        if node_script_path.is_file():
            log_file_path = BASE_DIR / "node.log"
            log_file = open(log_file_path, "w", encoding="utf-8")
            
            _kill_process_by_port(9050)
            
            node_process = subprocess.Popen(
                [python_exe, "node.py", "--port", "8090"],
                cwd=str(BASE_DIR),
                env=os.environ.copy(),
                stdout=log_file,
                stderr=log_file,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            time.sleep(3.0)
    
    server_thread = threading.Thread(target=start_fastapi, daemon=True)
    server_thread.start()

    api = Api()
    
    active_window = webview.create_window(
        "cool62coin Wallet", 
        text_select=True, 
        url="http://127.0.0.1:8081", 
        js_api=api, 
        width=1100, 
        height=790, 
        min_size=(900, 650)
    )

    active_window.events.closing += api.kill_local_node

    webview.start(icon=str(ICON_DIR))

if __name__ == '__main__':
    main()
