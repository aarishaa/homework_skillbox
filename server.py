import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n","")

                active_logins = self.get_active_logins()

                if login in active_logins:
                    self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                    self.transport.close()
                    self.server.clients.remove(self)
                else:
                    self.login = login
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.BaseTransport):
        self.server.clients.append(self)
        self.transport = transport

        print("Пришёл новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}:{content}\n"

        self.server.history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def get_active_logins(self):
        logins = []
        for client in self.server.clients:
            logins.append(client.login)
        return logins

    def send_history(self):
       for message in self.server.history:
            self.transport.write(message.encode())




class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
         loop = asyncio.get_running_loop()

         coroutine = await loop.create_server(
             self.build_protocol,
             '127.0.0.1',
             8888
         )

         print("Сервер запущен ...")
         await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
