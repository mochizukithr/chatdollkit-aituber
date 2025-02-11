import json
import socket
import traceback


class ChatdollKitClient:
    def __init__(self, host: str = "localhost", port: int = 8888):
        self.host = host
        self.port = port
        self.current_config = {
            "dialog": {"auto_pilot": {}},
            "model": {},
            "speech_synthesizer": {},
            "llm": {}
        }

    def update_current_config(self, endpoint: str, operation: str, *, text: str = None, payloads: dict = None):
        if endpoint == "dialog":
            if operation == "auto_pilot":
                del payloads["is_on"]
            else:
                return
        
        elif endpoint == "model":
            if operation == "perform":
                return

        self.current_config[endpoint][operation] = {"text": text, "payloads": payloads}

    def apply_config(self, config: dict):
        for endpoint, operation_kv in config.items():
            for operation, v in operation_kv.items():
                if v:
                    self.send_message(endpoint, operation, text=v["text"], payloads=v["payloads"])

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def close(self):
        self.client_socket.close()

    def send_message(self, endpoint: str, operation: str, *, text: str = None, priority: int = 10, payloads: dict = None):
        try:
            self.connect()

            message_dict = {
                "Endpoint": endpoint,
                "Operation": operation,
                "Text": text,
                "Priority": priority,
            }
            if payloads:
                message_dict["Payloads"] = payloads
            message = json.dumps(message_dict, ensure_ascii=False)

            self.client_socket.sendall((message + "\n").encode("utf-8"))
            print(f"Message sent: {message}")

            # Update current config
            self.update_current_config(endpoint, operation, text=text, payloads=payloads)

        except Exception as ex:
            print(f"Failed to send message: {ex}\n{traceback.format_exc()}")

        finally:
            self.close()

    def dialog(self, operation: str, text: str = None, data: dict = None, priority: int = 10):
        self.send_message("dialog", operation, text=text, payloads=data, priority=priority)

    def process_dialog(self, text: str, priority: int = 10):
        self.dialog("process", text=text, priority=priority)

    def clear_dialog_queue(self, priority: int = 0):
        self.dialog("clear", priority=priority)

    def model(self, operation: str, text: str = None, data: dict = None):
        self.send_message("model", operation, text=text, payloads=data)

    def config(self, data: dict):
        self.send_message("config", "apply", payloads=data)

    def speech_synthesizer(self, operation: str, data: dict):
        self.send_message("speech_synthesizer", operation, payloads=data)

    def llm(self, operation: str, data: dict):
        self.send_message("llm", operation, payloads=data)

    def reconnect(self, host: str = None, port: int = None):
        self.close()

        if self.host:
            self.host = host
        if self.port:
            self.port = port
        
        self.connect()
