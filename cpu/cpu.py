"""By: Simone Badaruddin
Duck Machine model DM2022 CPU
"""
import opcode

import context  # Python import search from project root
import cpu.memory
import instruction_set.instr_format
from instruction_set.instr_format import Instruction, OpCode, CondFlag, decode
from cpu.memory import Memory
from cpu.register import Register, ZeroRegister
from cpu.mvc import MVCEvent, MVCListenable

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ALU(object):
    """The arithmetic logic unit (also called a "functional unit"
    in a modern CPU) executes a selected function but does not
    otherwise manage CPU state. A modern CPU core may have several
    ALUs to boost performance by performing multiple operatons
    in parallel, but the Duck Machine has just one ALU in one core.
    """
    # The ALU chooses one operation to apply based on a provided
    # operation code.  These are just simple functions of two arguments;
    # in hardware we would use a multiplexer circuit to connect the
    # inputs and output to the selected circuitry for each operation.
    ALU_OPS = {
        OpCode.ADD: lambda x, y: x + y,
        OpCode.SUB: lambda x, y: x - y,
        OpCode.MUL: lambda x, y: x * y,
        OpCode.DIV: lambda x, y: x // y,
        #
        # For memory access operations load, store, the ALU
        # performs the address calculation
        OpCode.LOAD: lambda x, y: x + y,
        OpCode.STORE: lambda x, y: x + y,
        # Some operations perform no operation
        OpCode.HALT: lambda x, y: 0
    }

    def exec(self, op: OpCode, in1: int, in2: int) -> tuple[int, CondFlag]:
        try:
            result = (ALU.ALU_OPS[op](in1, in2))
            if result == 0:
                return (result, CondFlag.Z)
            if result < 0:
                return (result, CondFlag.M)
            if result > 0:
                return (result, CondFlag.P)
        except:
            return (0, CondFlag.V)


class CPUStep(MVCEvent):
    """CPU is beginning step with PC at a given address"""
    def __init__(self, subject: "CPU", pc_addr: int,
                 instr_word: int, instr: Instruction)-> None:
        self.subject = subject
        self.pc_addr = pc_addr
        self.instr_word = instr_word
        self.instr = instr


class CPU(MVCListenable):
    """Duck Machine central processing unit (CPU)
    has 16 registers (including r0 that always holds zero
    and r15 that holds the program counter), a few
    flag registers (condition codes, halted state),
    and some logic for sequencing execution.  The CPU
    does not contain the main memory but has a bus connecting
    it to a separate memory.
    """
    def __init__(self, memory: Memory):
        super().__init__()
        self.memory = memory  # Not part of CPU; what we really have is a connection
        self.registers = [ ZeroRegister(), Register(), Register(), Register(),
                                   Register(), Register(), Register(), Register(),
                                   Register(), Register(), Register(), Register(),
                                   Register(), Register(), Register(), Register() ]
        self.condition = CondFlag.ALWAYS
        self.halted = False
        self.alu = ALU()
        self.pc = self.registers[15]

    def step(self):
        """One fetch/decode/execute step"""
        instr_addr = self.registers[15].get()
        instr_word = self.memory.get(instr_addr)
        instr = decode(instr_word)

        reg_src1 = instr.reg_src1
        reg_src2 = instr.reg_src2

        self.notify_all(CPUStep(self, instr_addr, instr_word, instr))

        if self.condition.value & instr.cond.value != 0:
            left_operand = self.registers[reg_src1].get()
            right_operand = instr.offset + self.registers[reg_src2].get()
            self.pc.put(self.pc.get() + 1)
            value = self.alu.exec(instr.op, left_operand, right_operand)
            if instr.op == OpCode.STORE:
                num = self.registers[instr.reg_target].get()
                self.memory.put(value[0], num)
            elif instr.op == OpCode.LOAD:
                self.registers[instr.reg_target].put(self.memory.get(value[0]))
            elif instr.op == OpCode.HALT:
                self.halted = True
            else:
                self.registers[instr.reg_target].put(value[0])
                self.condition = value[1]
        else:
            self.pc.put(self.pc.get() + 1)

    def run(self, from_addr=0, single_step=False) -> None:
        """Step the CPU until it executes a HALT"""
        self.halted = False
        self.registers[15].put(from_addr)
        step_count = 0
        while not self.halted:
            if single_step:
                input(f"Step {step_count}; press enter")
            self.step()
            step_count += 1