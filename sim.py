#!/usr/bin/python3

"""
Arnik Shah
CS-UY 2214
October 27, 2024
sim.py
"""

from collections import namedtuple
import re
import argparse

# Some helpful constant values that we'll be using.
Constants = namedtuple("Constants",["NUM_REGS", "MEM_SIZE", "REG_SIZE"])
constants = Constants(NUM_REGS = 8,
                      MEM_SIZE = 2**13,
                      REG_SIZE = 2**16)

def load_machine_code(machine_code, mem):
    """
    Loads an E20 machine code file into the list
    provided by mem. We assume that mem is
    large enough to hold the values in the machine
    code file.
    sig: list(str) -> list(int) -> NoneType
    """
    machine_code_re = re.compile("^ram\[(\d+)\] = 16'b(\d+);.*$")
    expectedaddr = 0
    for line in machine_code:
        match = machine_code_re.match(line)
        if not match:
            raise ValueError("Can't parse line: %s" % line)
        addr, instr = match.groups()
        addr = int(addr,10)
        instr = int(instr,2)
        if addr != expectedaddr:
            raise ValueError("Memory addresses encountered out of sequence: %s" % addr)
        if addr >= len(mem):
            raise ValueError("Program too big for memory")
        expectedaddr += 1
        mem[addr] = instr

def print_state(pc, regs, memory, memquantity):
    """
    Prints the current state of the simulator, including
    the current program counter, the current register values,
    and the first memquantity elements of memory.
    sig: int -> list(int) -> list(int) - int -> NoneType
    """
    print("Final state:")
    print("\tpc="+format(pc,"5d"))
    for reg, regval in enumerate(regs):
        print(("\t$%s=" % reg)+format(regval,"5d"))
    line = ""
    for count in range(memquantity):
        line += format(memory[count], "04x")+ " "
        if count % 8 == 7:
            print(line)
            line = ""
    if line != "":
        print(line)

def getOpCode(instr):
    """
    Extract Opcode
    sig: int -> int
    """
    code = instr >> 13
    return code & 0b111

def getLastFourBits(instr):
    """
    Get last four bits
    sig: int -> int
    """
    return instr & 0b1111

def getLastSevenBits(instr):
    """
    Get last seven bits unsigned
    sig: int -> int
    """
    num = instr & 0b111111
    isNeg = instr & 0b1000000
    if isNeg:
        num -= 2**6
    return num

def getLastSevenBitsUnsigned(instr):
    """
    Get last seven bits signed
    sig: int -> int
    """
    return instr & 0b1111111

def getLastThirteenBits(instr):
    """
    Get last thirteen bits
    sig: int -> int
    """
    return instr & 0b1111111111111

def incPC(pc):
    """
    increment pc
    sig: int -> int
    """
    return fixPC(pc + 1)

def fixPC(pc):
    """
    get pc in range
    sig: int -> int
    """
    if pc >= constants.MEM_SIZE:
        pc -= constants.MEM_SIZE
    elif pc < 0:
        pc = constants.MEM_SIZE + pc
    return pc

def getRegALocation(instr):
    """
    Get regA location
    sig: int -> int
    """
    code = instr >> 10
    return code & 0b111

def getRegBLocation(instr):
    """
    Get regB location
    sig: int -> int
    """
    code = instr >> 7
    return code & 0b111

def getRegCLocation(instr):
    """
    Get regC location
    sig: int -> int
    """
    code = instr >> 4
    return code & 0b111

def makeUnsigned(val):
    """
    make signed num
    sig: int -> int
    """
    if val >= constants.REG_SIZE:
        val = val - constants.REG_SIZE
    elif val < 0:
        val = constants.REG_SIZE + val
    return val


def main():
    parser = argparse.ArgumentParser(description='Simulate E20 machine')
    parser.add_argument('filename', help='The file containing machine code, typically with .bin suffix')
    cmdline = parser.parse_args()

    with open(cmdline.filename) as file:
        # Load file and parse using load_machine_code
        memory = [0000000000000000] * constants.MEM_SIZE
        load_machine_code(file, memory)
        
    # intialize program counter and registers
    pc = 0
    regs = [0] * constants.NUM_REGS 

    # E20 Simulation
    while True:
        # Get OpCode
        addr = memory[pc]
        opCode = getOpCode(addr)
        # For instructions add, sub, or, and, slt, jr, nop
        if opCode == 0:
            regA = getRegALocation(addr)
            regB = getRegBLocation(addr)
            regC = getRegCLocation(addr)
            # Get last four bit to determine operation
            lastFour = getLastFourBits(addr)
            # Skip if you try to edit $0
            if regC == 0 and (lastFour == 0 or lastFour == 1 or lastFour == 2 or lastFour == 3 or lastFour == 4):
                pc = incPC(pc)
                continue
            # add opCode
            if lastFour == 0:
                regs[regC] = makeUnsigned(regs[regA] + regs[regB])
                pc = incPC(pc)
            # sub opCode
            elif lastFour == 1:
                regs[regC] = makeUnsigned(regs[regA] - regs[regB])
                pc = incPC(pc)
            # or opCode
            elif lastFour == 2:
                regs[regC] = makeUnsigned(regs[regA] | regs[regB])
                pc = incPC(pc)
            # and opCode
            elif lastFour == 3:
                regs[regC] = makeUnsigned(regs[regA] & regs[regB])
                pc = incPC(pc)
            # slt opCode
            elif lastFour == 4:
                regs[regC] = 1 if regs[regA] < regs[regB] else 0
                pc = incPC(pc)
            # jr opCode
            else:
                pc = getLastThirteenBits(regs[regA])
        # For instruction addi, movi
        elif opCode == 1:
            regSrc = getRegALocation(addr)
            regDst = getRegBLocation(addr)
            imm = getLastSevenBits(addr)
            # Skip if you try to edit $0
            if regDst == 0:
                pc = incPC(pc)
                continue
            regs[regDst] = makeUnsigned(regs[regSrc] + imm)
            pc = incPC(pc)
        # For instructions j, halt
        elif opCode == 2:
            prevPC = pc
            pc = fixPC(getLastThirteenBits(addr))
            # halt program
            if prevPC == pc:
                break
        # For instructions jal
        elif opCode == 3:
            regs[7] = pc + 1
            pc = fixPC(getLastThirteenBits(addr))
        # For instructions lw
        elif opCode == 4:
            regDst = getRegBLocation(addr)
            regSrc = getRegALocation(addr)
            imm = getLastSevenBits(addr)
            if regDst == 0:
                pc = incPC(pc)
                continue
            loc = regs[regSrc] + imm
            loc = getLastThirteenBits(loc)
            regs[regDst] = makeUnsigned(memory[loc])
            pc = incPC(pc)
        # For instructions sw
        elif opCode == 5:
            regSrc = getRegBLocation(addr)
            regAddr = getRegALocation(addr)
            imm = getLastSevenBits(addr)
            loc = regs[regAddr] + imm
            loc = getLastThirteenBits(loc)
            memory[loc] = regs[regSrc]
            pc = incPC(pc)
        # For instructions jeq
        elif opCode == 6:
            regA = getRegALocation(addr)
            regB = getRegBLocation(addr)
            if regs[regA] == regs[regB]:
                pc = fixPC(getLastSevenBits(addr) + pc + 1)
            else:
                pc = incPC(pc)
        # opCode == 7, for instructions slti
        else:
            regSrc = getRegALocation(addr)
            regDst = getRegBLocation(addr)
            imm = getLastSevenBitsUnsigned(addr)
            if regDst == 0:
                pc = incPC(pc)
                continue
            regs[regDst] = 1 if regs[regSrc] < imm else 0
            pc = incPC(pc)

    # Print the final state of the simulator before ending
    print_state(pc, regs, memory, 128)
if __name__ == "__main__":
    main()