#! /usr/bin/env python3

import os, stat
from sys import argv


class OBFramer:
    def __init__(self,filename,fd,output=1):
        reader =  BufferedReader(fd)
        writer =  BufferedWriter(output)
        
        filename_header = len(filename).to_bytes(8,'big')
        writer.buf[writer.index:(writer.index+len(filename_header))] = filename_header
        writer.index+=len(filename_header)
        
        filename_b = filename.encode()
        writer.buf[writer.index:(writer.index+len(filename_b))] = filename_b
        writer.index+=len(filename_b)
        
        fileheader = os.lseek(fd,0,os.SEEK_END).to_bytes(32,'big')
        os.lseek(fd,0,0)
        writer.buf[writer.index:(writer.index+len(fileheader))] = fileheader
        writer.index+=len(fileheader)
        
        byte = reader.readByte()

        while(byte!=None):
            writer.writeByte(byte)
            byte = reader.readByte()
        
        writer.flush()
        reader.close()
    
    def startFrame(self,numBytes):
        pass
    def writeFrame(self,byteArray):
        pass
    def endFrame(self):
        pass
    def closeFrame(self):
        pass

class OBDeframer:
    def __init__(self,fd=0):
        reader = BufferedReader(fd)
        while(True):
            nofiles = False
            print(reader.buf)
            filename_len = bytearray(8)
            for i in range(8):
                byte = reader.readByte()
                print(byte)
                if byte==None:
                    nofiles = True
                    break
                filename_len[i] = byte
            #print(nofiles)
            #print(reader.buf)
            if nofiles:
                break
            
            filename_len = int.from_bytes(filename_len,'big')
            if (filename_len)==0:
                break
            
            filename = bytearray(filename_len)
            for i in range(filename_len):
                filename[i] = reader.readByte()
        
            filename = filename.decode()
                
            file_len = bytearray(32)
            for i in range(32):
                file_len[i] = reader.readByte()
                #index+=1
            file_len = int.from_bytes(file_len,'big')
            
            write_fd = os.open(filename, os.O_WRONLY| os.O_CREAT| os.O_TRUNC)
            writer = BufferedWriter(write_fd)
            for i in range(file_len):
                byte = reader.readByte()
                print(byte)
                writer.writeByte(byte)
            
            writer.flush()
            print("writer flushed")
        reader.close()
        print("reader closed")
    def startDeframer(self,byteArray):
        pass
    def readDeframe(self,numBytes):
        pass
    def endDeframer(self):
        pass
    def closeDeframer(self):
        pass

class IBFramer:
    def __init__(self,filename,fd):
        reader =  BufferedReader(fd)
        writer =  BufferedWriter(1)
        ender = "`e".encode()
        filename_b = bytearray((len(filename)*2)+2)
        i = 0
        for letter in filename:
            if letter == "`":
                letter = "``"
            filename_b[i:i+len(letter)] = letter.encode()
            i+= len(letter)
            
        writer.buf[writer.index:(writer.index+i)] = filename_b[0:i]
        writer.index+=i
        
        writer.buf[writer.index:(writer.index+len(ender))] = ender
        writer.index+= len(ender)
        
        byte = reader.readByte()
        
        while(byte!=None):
            if (byte == "`".encode()[0]):
                writer.writeByte(byte)
                writer.writeByte(byte)
            else:
                writer.writeByte(byte)
            byte = reader.readByte()
        
        writer.buf[writer.index:(writer.index+len(ender))] = ender
        writer.index+=len(ender)
            
        writer.flush()
        reader.close()
    
    def startFrame(self,numBytes):
        pass
    def writeFrame(self,byteArray):
        pass
    def endFrame(self):
        pass
    def closeFrame(self):
        pass

class IBDeframer:
    def __init__(self,fd):
                    
        reader =  BufferedReader(fd)

        while(True):
            filename = bytearray(512)
            i = 0
       
            byte = reader.readByte()
            while(byte!=None):
                if(byte == "`".encode()[0]):
                    nextbyte = reader.readByte()
                    if(nextbyte==None):
                         os.write(2,"Corrupt Inband File, please try again\n".encode())
                         exit()
                    if(nextbyte=="e".encode()[0]):
                        break
                    filename[i]=nextbyte
                else:
                    filename[i]=byte
                byte = reader.readByte()
                i += 1
            
            filename = filename[0:i].decode()
            if not filename:
                break
            
            write_fd = os.open(filename, os.O_WRONLY| os.O_CREAT| os.O_TRUNC)
            writer = BufferedWriter(write_fd)

            #i = 0
            byte = reader.readByte()
            while(byte!=None):
                if(byte == "`".encode()[0]):
                    nextbyte = reader.readByte()
                    if(nextbyte==None):
                        os.write(2,"Corrupt Inband File, please try again\n".encode())
                        exit()
                    if(nextbyte=="e".encode()[0]):
                        break
                    writer.writeByte(nextbyte)
                else:
                    writer.writeByte(byte)
                byte = reader.readByte()
                #i+=1
                        
            writer.flush()
            
        reader.close()
        
    def startDeframer(self,byteArray):
        pass
    def readDeframe(self,numBytes):
        pass
    def endDeframer(self):
        pass
    def closeDeframer(self):
        pass
    
class BufferedWriter:
    def __init__(self,fd, bufLen = 1024):
        self.fd = fd
        self.buf = bytearray(bufLen)
        self.index = 0
    def writeByte(self,byte):
        self.buf[self.index] = byte
        self.index += 1
        if self.index >= len(self.buf):
            self.flush()
    def flush(self):
        startIndex, endIndex = 0, self.index
        while startIndex < endIndex:
            nWritten = os.write(self.fd,self.buf[startIndex:endIndex])
            if nWritten == 0:
                os.write(2,f"buf.BufferedFDWriter(fd={self.fd}): flush failed\n".encode())
                sys.exit(1)
            startIndex += nWritten
        self.index = 0
    def close(self):
        self.flush()
        os.close(self.fd)
        
class BufferedReader:
    def __init__(self,fd, bufLen = 1024):
        self.fd = fd
        self.buf = b""
        self.index = 0
        self.bufLen = bufLen
    def readByte(self):
        if self.index >= len(self.buf):
            self.buf = os.read(self.fd,self.bufLen)
            self.index = 0
        if len(self.buf) == 0:
            return None
        else:
            retval = self.buf[self.index]
            self.index += 1
            return retval
    def close(self):
        os.close(self.fd)
    
if __name__ == '__main__':
    
    if len(argv)<2:
        os.write(2,"Insufficient commands\n".encode())
        exit()
    command = argv[1]
    if(command[0].lower()=="c"):
        i=2
        while(i<len(argv)):
            if(argv[i]=="<" or argv[i]==">"):
                break
            fd = os.open(argv[i] , os.O_RDONLY )
            if len(command)>1:
                if command[1]=="i":
                    IBFramer(argv[i],fd)
                elif command[1]=="o":
                    OBFramer(argv[i],fd)
                else:
                    os.write(2,"Incorrect command, please try again\n".encode())
                    exit()
            else:
                OBFramer(argv[i],fd)
            i+=1
    
    elif(command[0].lower()=="x"):
        i=2
        if (i>=len(argv)):
            if len(command)>1:
                if command[1]=="i":
                    IBDeframer(0)
                elif command[1]=="o":
                    OBDeframer(0)
                else:
                    os.write(2,"Incorrect command, please try again\n".encode())
                    exit()
            else:
                OBDeframer()
        while(i<len(argv)):
            if(argv[i]=="<" or argv[i]==">"):
                break
            fd = os.open(argv[i] , os.O_RDONLY)
            if len(command)>1:
                if command[1]=="i":
                    IBDeframer(fd)
                elif command[1]=="o":
                    OBDeframer(fd)
                else:
                    os.write(2,"Incorrect command, please try again\n".encode())
                    exit()
            else:
                OBDeframer(fd)
            i+=1
        
    
    #filename = argv[1]
    #size = str(os.path.getsize(filename))+"\n"
    #os.write(2,size.encode())


