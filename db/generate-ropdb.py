#!/usr/bin/env python3
from ropper import RopperService
import sys

rs = RopperService()
rs.options.color = True
rs.options.detailed = True

binname = sys.argv[1]
dbname = sys.argv[2]

binfile = open(binname, 'rb')
binary = binfile.read()
binfile.close()


rs.addFile("arm", bytes=binary, raw=True, arch="ARM")
rs.addFile("thumb", bytes=binary, raw=True, arch="ARMTHUMB")
rs.setImageBaseFor(name="arm", imagebase=0x100000)
rs.setImageBaseFor(name="thumb", imagebase=0x100000)

print("Loading gadgets for", binname)
rs.loadGadgetsFor()

dbfile = open(dbname, 'w')

def add_raw_gadget(name, addr):
    dbfile.write(name + " = " + hex(addr) + "\n")

def add_gadget(name, pattern):
    result = rs.search(search=pattern)
    try:
        file, gadget = next(result)
        print("Found", name)
        print(gadget)
        add_raw_gadget(name, gadget.address if file is 'arm' else gadget.address+1)
    except:
        print(pattern, "not found!")

def add_inst(name, pattern, offset=0):
    result = rs.searchInstructions(pattern)
    try:
        file, inst = result.popitem()
        if not inst:
            file, inst = result.popitem()
        addr = inst[0].address+offset if file is 'arm' else inst[0].address+offset+1
        print("Found", name, "@"+hex(addr)+",", "relevant part:")
        print(inst[0])
        add_raw_gadget(name, addr)
    except:
        print(pattern, "not found!")


add_gadget('NOP', 'pop {pc}')
add_gadget('POP_R0PC', 'pop {r0, pc}')
add_gadget('POP_R0R1R2R3R4PC', 'pop {r0, r1, r2, r3, r4, pc}')
add_gadget('POP_R1PC', 'pop {r1, pc}')
add_gadget('POP_R1R2R3PC', 'pop {r1, r2, r3, pc}')
add_gadget('POP_R2R3PC', 'pop {r2, r3, pc}')
add_gadget('POP_R3PC', 'pop {r3, pc}')
add_gadget('POP_R4PC', 'pop {r4, pc}')
add_gadget('POP_R4R5PC', 'pop {r4, r5, pc}')
add_gadget('POP_R4R5R6PC', 'pop {r4, r5, r6, pc}')
add_gadget('POP_R4R5R6R7PC', 'pop {r4, r5, r6, r7, pc}')

add_inst('CMP_R0R1_MOVSNE_R0_0_MOVSEQ_R0_1_POP_R4PC', 'cmp r0, r1; bne #8; movs r0, #1; pop {r4, pc}; movs r0, #0; pop {r4, pc}')

add_gadget('LDR_R0R0_POP_R4PC', 'ldr r0, [r0]; pop {r4, pc}')

add_gadget('STR_R0R4_POP_R4PC', 'str r0, [r4]; pop {r4, pc}')
add_gadget('STR_R1R0_POP_R4PC', 'str r1, [r0]; pop {r4, pc}')

add_gadget('ADDS_R0R0R1_POP_R4PC', 'adds r0, r0, r1; pop {r4, pc}')
add_gadget('ADDS_R0R0_4_POP_R4PC', 'adds r0, r0, #4; pop {r4, pc}')

add_gadget('ADD_R0R0_80_STR_R1R0_POP_R4PC', 'adds r0, #0x80; str r1, [r0]; pop {r4, pc}')

add_gadget('MOV_SPR0_MOV_R0R2_MOV_LRR3_BX_R1', 'mov sp, r0; mov r0, r2; mov lr, r3; bx r1')
add_gadget('MOV_LRR3_BX_R1', 'mov lr, r3; bx r1')

add_gadget('MUL_R0R4R0_POP_R4PC', 'muls r0, r4, r0; pop {r4, pc}')



add_inst('PTM_SENDSYNCREQ_POP_R2R3R4PC', \
"""
cmp r0, #0;
blt #8;
ldr r0, [sp, #4];
ldr r0, [r0, #4];
pop {r2, r3, r4, pc};
.hword 0;
.word 0x403
""", -8)

add_inst('SRV_REGISTERSERVICE', \
"""
adds r0, #0x80;
str r0, [sp, #4];
movs r0, #0;
mov r3, r0;
str r0, [sp];
movs r2, #4;
movs r1, #3;
add r0, sp, #4
""", -0xE)
add_inst('SRV_GETSERVICEHANDLE', \
"""
cmp r4, #0;
bgt 0xc;
movs r1, #0x7f;
lsls r1, r1, #3;
movs r0, #5;
b 0xC;
cmp r2, #8;
ble 0x12;
movs r1, #5;
movs r0, #8
""", -0x6)

add_inst('GET_THREAD_LOCAL_STORAGE', \
"""
mrc p15, 0, r0, c13, c0, 3;
bx lr
""")

add_inst('SVC_SLEEPTHREAD', 'svc 0xA; bx lr')
add_inst('SVC_EXITTHREAD', 'svc 9; bx lr')
add_inst('SVC_CREATETHREAD', \
"""
push {r0, r4};
ldr r0, [sp, #8];
ldr r4, [sp, #12];
svc 8;
ldr r2, [sp];
str r1, [r2];
add sp, sp, #4;
pop {r4};
bx lr
""")
add_inst('SVC_CONTROLMEMORY', \
"""
push {r0, r4};
ldr r0, [sp, #8];
ldr r4, [sp, #12];
svc 1;
ldr r2, [sp];
str r1, [r2];
add sp, sp, #4;
pop {r4};
bx lr
""")
add_inst('SVC_ACCEPTSESSION', \
"""
str r0, [sp, #-4]!;
svc 0x4A;
ldr r2, [sp];
str r1, [r2];
add sp, sp, #4;
bx lr
""")
add_inst('SVC_SENDSYNCREQUEST', \
"""
svc 0x32;
bx lr
""")
add_inst('SVC_REPLYANDRECEIVE', \
"""
str r0, [sp, #-4]!;
svc 0x4A;
ldr r2, [sp];
str r1, [r2];
add sp, sp, #4;
bx lr
""")

add_inst('MEMCPY', \
"""
cmp r2, #8;
bhi #0xc8;
beq #0xb4;
cmp r2, #4;
bhi #0x4c;
beq #0x80;
cmp r2, #2;
bcc #0x38;
beq #0x74;
ldrh r2, [r1], #2;
ldrb r3, [r1], #1;
strh r2, [r0], #2;
strb r3, [r0], #1;
""")

add_inst('MEMSET', \
"""
and r3, r2, #0xFF
""")

dbfile.close()
