# network.py
# 負責處理區域網路連線 (TCP Socket)
# [修正版] 加入 Timeout 機制，防止視窗卡死

import socket
import threading

class NetworkManager:
    def __init__(self):
        self.client = None
        self.server = None
        self.connected = False
        self.received_data = None 
        self.is_host = False
        self.peer_addr = None

    def get_local_ip(self):
        """嘗試獲取本機的區網 IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def create_server(self, port=5555):
        """建立房間 (Host)"""
        self.is_host = True
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('0.0.0.0', port))
            self.server.listen(1)
            
            # [關鍵修正] 設定 Timeout 為 0.05 秒
            # 這樣 accept() 最多只會卡住 0.05 秒，不會讓視窗當機
            self.server.settimeout(0.05)
            
            print(f"[Network] Server started. Waiting on {self.get_local_ip()}:{port}")
            return True
        except Exception as e:
            print(f"[Network] Create server failed: {e}")
            return False

    def wait_for_connection(self):
        """
        等待對手連線
        因為有設定 settimeout，這裡不會永久卡死
        """
        if not self.server: return False
        try:
            conn, addr = self.server.accept()
            
            # 連線成功後，把 client socket 改回阻塞模式或保持原本設定
            # 這裡建議改回 None (阻塞) 或較長的 timeout 以便傳輸穩定
            conn.settimeout(None) 
            
            self.client = conn
            self.peer_addr = addr
            self.connected = True
            print(f"[Network] Player connected from {addr}")
            
            # 開啟監聽執行緒
            threading.Thread(target=self._receive_data, daemon=True).start()
            return True
            
        except socket.timeout:
            # [關鍵] 如果超時(沒人連)，就回傳 False，讓主程式繼續跑迴圈畫畫面
            return False
        except Exception as e:
            print(f"Wait connection error: {e}")
            return False

    def connect_to_server(self, ip, port=5555):
        """加入房間 (Client)"""
        self.is_host = False
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Client 連線也可以設個 timeout 避免卡太久，但通常 connect 很快
            self.client.settimeout(5.0) 
            self.client.connect((ip, port))
            self.client.settimeout(None) # 連上後恢復正常模式
            
            self.connected = True
            print(f"[Network] Connected to {ip}:{port}")
            
            threading.Thread(target=self._receive_data, daemon=True).start()
            return True
        except Exception as e:
            print(f"[Network] Connection failed: {e}")
            return False

    def _receive_data(self):
        """背景執行緒：持續接收資料"""
        while self.connected:
            try:
                data = self.client.recv(1024).decode('utf-8')
                if not data:
                    print("[Network] Disconnected")
                    self.connected = False
                    break
                print(f"[Network] Received: {data}")
                self.received_data = data 
            except:
                self.connected = False
                break

    def send(self, data):
        """傳送字串資料"""
        if self.connected and self.client:
            try:
                self.client.send(str(data).encode('utf-8'))
            except:
                print("[Network] Send failed")
                self.connected = False

    def close(self):
        self.connected = False
        if self.client: self.client.close()
        if self.server: self.server.close()