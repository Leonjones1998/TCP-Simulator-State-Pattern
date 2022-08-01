import socket
from State import *
import random
import json
import time
import sys

SIZE = 4096
SERVER = "172.19.233.130"
PORT = 54366
SEQ_NO = random.randint(0, 9999)


class Closed(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def active_open(self):
        print("[Connecting] Actively Initiating The Connection")
        self.CurrentContext.Socket()
        print("[Connected] Connection Made")
        self.CurrentContext.SendSyn()
        print("[Setting State] Setting Server State To Syn Sent")
        self.CurrentContext.setState("SYNSENT")
        return True


class SynSent(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def syn_ack(self):
        self.CurrentContext.StoreData()
        self.CurrentContext.CheckPacket()
        self.CurrentContext.SendAck()
        print("[Setting State] Setting Server State To Established")
        self.CurrentContext.setState("ESTABLISHED")
        return True

    def trigger(self):
        self.CurrentContext.syn_ack()

    def rst(self):
        pass

    def timeout(self):
        pass


class Established(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def close(self):
        self.CurrentContext.SendMessage()
        self.CurrentContext.SendFin()
        print("Setting State To FinWait1")
        self.CurrentContext.setState("FINWAIT1")
        return True

    def trigger(self):
        self.close()

    def rst(self):
        pass


class FinWait1(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def fin2(self):
        print("here")
        self.CurrentContext.StoreData()
        print("here")
        self.CurrentContext.CheckPacket()
        print("Ack Number Received")
        print("Setting State To FinWait2")
        self.CurrentContext.setState("FINWAIT2")
        return True

    def trigger(self):
        self.fin2()


class FinWait2(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def ack(self):
        self.CurrentContext.StoreData()
        self.CurrentContext.CheckPacket()
        print("Fin Number Received")
        self.CurrentContext.SendAck()
        print("Ack Sent Back To Server")
        print("Setting State To TimedWait")
        self.CurrentContext.setState("TIMEDWAIT")
        return True

    def trigger(self):
        self.ack()


class TimedWait(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def timeout(self):
        self.CurrentContext.CloseConnection()
        print("Closing The Connection and Restarting The Program")
        self.CurrentContext.setState("CLOSED")

    def trigger(self):
        self.timeout()




class Client(StateContext, Transition):
    def __init__(self):
        self.host = SERVER
        self.port = PORT
        self.C_Sock = None
        self.seq = SEQ_NO
        self.connection = None
        self.conSeq = None
        self.clientSeq = None

        print(f"[Server Sequence Number] {self.seq}")

        self.availableStates["CLOSED"] = Closed(self)
        self.availableStates["SYNSENT"] = SynSent(self)
        self.availableStates["ESTABLISHED"] = Established(self)
        self.availableStates["FINWAIT1"] = FinWait1(self)
        self.availableStates["FINWAIT2"] = FinWait2(self)
        self.availableStates["TIMEDWAIT"] = TimedWait(self)
        self.setState("CLOSED")

    def active_open(self):
        self.CurrentState.active_open()

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
        self.C_Sock = socket.socket()
        try:
            self.C_Sock.connect((self.host, self.port))
            print("[Connected] Connection Made")
        except Exception as err:
            print("[System Error] Socket Couldn't Be Created.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()

    def StoreData(self):
        self.dataString = self.C_Sock.recv(SIZE)
        self.dataString = self.dataString.decode()
        self.dataArray = self.dataString.split(',')

        self.synD = self.dataArray[0][3:]
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
        elif int(self.synD) == 1 and int(self.ackD) == self.seq:
            self.conSeq = int(self.clientSeq)
            print(f"[Received SYN + ACK] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
        elif int(self.finD) == 1:
            self.conSeq = int(self.clientSeq)
            print(f"[Received FIN] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
        else:
            print(f"[Failed] SYN: {self.synD} ACK: {self.ackD} SEQ: {self.clientSeq} FIN: {self.finD}")
            exit()

    def SendSyn(self):
        print(f"[Sending] Syn")
        synString = f"SYN1,ACK0,SEQ{self.seq},FIN0"
        try:
            self.C_Sock.send(synString.encode())
        except Exception as err:
            print("[System Error] Packet Couldn't Be Sent.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()
        self.seq += 1

    def SendAck(self):
        print(f"[Sending] Ack")
        ackString = f"SYN0,ACK{self.conSeq + 1},SEQ{self.seq},FIN0"
        try:
            self.C_Sock.send(ackString.encode())
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
            self.C_Sock.send(finString.encode())
        except Exception as err:
            print("[System Error] Packet Couldn't Be Sent.")
            print(err)
            print("[Exiting] Now Exiting The Program.")
            exit()
        self.seq += 1

    def SendMessage(self):
        dump = input("Message: ")
        json.dumps(dump)
        while dump != "test":
            time.sleep(2)
            dump = input("Message: ")
            json.dumps(dump)
            self.C_Sock.sendall(bytes(dump, encoding="utf-8"))
        rec_message = self.C_Sock.recv(SIZE)
        print(rec_message)

    def CloseConnection(self):
        print("[Connection] Closing Connection.")
        self.C_Sock.close()


def Main():
    MyClient = Client()
    MyClient.active_open()


if __name__ == '__main__':
    while True:
        print("Would you like to Begin?")
        y = input("Type Yes To Begin: ")
        if y == "Yes":
            Main()
        else:
            break

