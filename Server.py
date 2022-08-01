import socket
from State import *
import time
import sys
import random
import json

SIZE = 1024
SERVER = "192.168.1.182"
PORT = 15699
SEQ_NO = random.randint(0, 9999)


class Closed(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def passive_open(self):
        print("Passively Opening The Server")
        print("Setting Server State To Listen")
        self.CurrentContext.setState("LISTEN")
        return True

    def rst(self):
        pass


class Listen(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def syn(self):
        self.CurrentContext.Socket()
        self.CurrentContext.StoreData()
        self.CurrentContext.CheckPacket()
        print("Syn Number Received")
        self.CurrentContext.SendSynAck()
        print("Syn & Ack Sent Back To Client")
        print("Setting Server State To Syn Received")
        self.CurrentContext.setState("SYNRECVD")

        return True

    def trigger(self):
        self.CurrentContext.syn()

    def rst(self):
        pass


class SynRecvd(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def ack(self):
        self.CurrentContext.StoreData()
        self.CurrentContext.CheckPacket()
        print("Ack Number Received")
        print("Setting Server State To Established")
        self.CurrentContext.setState("ESTABLISHED")
        return True

    def trigger(self):
        self.CurrentContext.ack()

    def rst(self):
        pass


class Established(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def fin(self):
        self.CurrentContext.StoreData()
        self.CurrentContext.CheckPacket()
        print("Fin Number Received")
        self.CurrentContext.SendAck()
        print("Ack Sent Back To Client")
        print("Setting Server State To Close Wait")
        self.CurrentContext.setState("CLOSEWAIT")
        return True

    def trigger(self):
        self.fin()

    def rst(self):
        pass


class CloseWait(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def close(self):
        time.sleep(3)
        print("Close Command Received")
        self.CurrentContext.SendFin()
        print("Fin Sent To Client")
        print("Setting Server State To Last Ack")
        self.CurrentContext.setState("LASTACK")
        return True

    def trigger(self):
        self.close()

    def rst(self):
        pass


class LastAck(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def ack(self):
        self.CurrentContext.StoreData()
        self.CurrentContext.CheckPacket()
        print("Final Ack Received from Client")
        print("Closing The Connection and Restarting The Program")
        self.CurrentContext.CloseConnection()
        self.CurrentContext.setState("CLOSED")
        return True

    def trigger(self):
        self.ack()

    def rst(self):
        pass


class Server(StateContext, Transition):
    def __init__(self):
        self.host = SERVER
        self.port = PORT
        self.S_Sock = None
        self.seq = SEQ_NO
        self.connection = None
        self.conSeq = None
        self.clientSeq = None

        print(f"[Server Sequence Number] {self.seq}")

        self.availableStates["CLOSED"] = Closed(self)
        self.availableStates["LISTEN"] = Listen(self)
        self.availableStates["SYNRECVD"] = SynRecvd(self)
        self.availableStates["ESTABLISHED"] = Established(self)
        self.availableStates["CLOSEWAIT"] = CloseWait(self)
        self.availableStates["LASTACK"] = LastAck(self)
        self.setState("CLOSED")

    def passive_open(self):
        self.CurrentState.passive_open()

    def syn(self):
        self.CurrentState.syn()

    def ack(self):
        self.CurrentState.ack()

    def rst(self):
        self.CurrentState.rst()

    def syn_ack(self):
        self.CurrentState.syn_ack()

    def close(self):
        self.CurrentState.close()

    def fin(self):
        self.CurrentState.fin()

    def timeout(self):
        self.CurrentState.timeout()

    def Socket(self):
        self.S_Sock = socket.socket()
        try:
            self.S_Sock.bind((self.host, self.port))
            self.S_Sock.listen(1)
            print("Waiting for a Client to Connect")
            self.connection, connAddr = self.S_Sock.accept()
            print(f"Connection from {connAddr}")
        except Exception as err:
            print("[System Error] Socket Couldn't Be Created.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()

    def StoreData(self):
        self.dataString = self.connection.recv(SIZE)
        self.dataString = self.dataString.decode()
        print(self.dataString)
        self.dataArray = self.dataString.split(',')
        print(self.dataArray)

        self.synD = self.dataArray[0][3:]
        print(self.synD)
        self.ackD = self.dataArray[1][3:]
        self.clientSeq = self.dataArray[2][3:]
        self.finD = self.dataArray[3][3:]

    def CheckPacket(self):
        if int(self.synD) == 1 and int(self.ackD) == 0:
            self.conSeq = int(self.clientSeq)
            print(f"[Received SYN] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
        elif int(self.synD) == 0 and int(self.ackD) == self.seq:
            self.conSeq = int(self.clientSeq)
            print(f"[Received ACK] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
        elif int(self.finD) == 1:
            self.conSeq = int(self.clientSeq)
            print(f"[Received FIN] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
        else:
            print(f"[Failed] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
            exit()

    def SendSynAck(self):
        print(f"[Sending] SynAck")
        synAckString = f"SYN1,ACK{self.conSeq + 1},SEQ{self.seq},FIN0"
        try:
            self.connection.send(synAckString.encode())
        except Exception as err:
            print("[System Error] Packet Couldn't Be Sent.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()
        self.seq += 1

    def SendAck(self):
        print("[Sending] Ack")
        ack = f"SYN0,ACK{self.conSeq + 1},SEQ{self.seq},FIN0"
        try:
            self.connection.send(ack.encode())
        except Exception as err:
            print("[System Error] Packet Couldn't Be Sent.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()
        self.seq += 1

    def SendFin(self):
        print(f"[Sending] Fin")
        finString = f"SYN0,ACK0,SEQ{self.seq},FIN1"
        try:
            self.connection.send(finString.encode())
        except Exception as err:
            print("[System Error] Packet Couldn't Be Sent.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()
        self.seq += 1

    def CloseConnection(self):
        print("[Connection] Closing Connection.")
        self.S_Sock.close()


def Main():
    MyServer = Server()
    MyServer.passive_open()


if __name__ == '__main__':
        Main()