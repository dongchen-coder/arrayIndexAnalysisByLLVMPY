#http://www.llvmpy.org/llvmpy-doc/0.9/doc/llvm.core.Builder.html
#http://sourcecodebrowser.com/llvm-py/0.6/classllvm_1_1core_1_1_type.html

from llvm import *
from llvm.core import *

from llpython import *

mod = Module.new('gpuRaceDetection')

#char = int(8)
charty = Type.pointer(Type.int(8))

intty = Type.int(32)
int64ty = Type.int(64)

fnty = Type.function(Type.void(), [intty, intty, charty, intty, charty, charty])
fnty2 = Type.function(Type.void(), [intty, charty, charty, intty])
fnty3 = Type.function(Type.void(), [])

region_copy = Function.new(mod,fnty, name='region_copy')
warp_level_parallel_memcpy = Function.new(mod, fnty2, name='warp_level_parallel_memcpy')
syncthreads = Function.new(mod, fnty3, name='__syncthreads')

#define void @region_copy(i32 %block_id, i32 %tid, i8* %orig_copy, i32 %size, i8* %new_copy, i8* %union_copy) #0 {
#    %1 = alloca i32, align 4
#    %2 = alloca i32, align 4
#    %3 = alloca i8*, align 8
#   %4 = alloca i32, align 4
#    %5 = alloca i8*, align 8
#    %6 = alloca i8*, align 8
#    store i32 %block_id, i32* %1, align 4
#    store i32 %tid, i32* %2, align 4
#    store i8* %orig_copy, i8** %3, align 8
#    store i32 %size, i32* %4, align 4
#    store i8* %new_copy, i8** %5, align 8
#    store i8* %union_copy, i8** %6, align 8
#    %7 = load i32* %2, align 4
#    %8 = load i8** %5, align 8
#    %9 = load i8** %3, align 8
#    %10 = load i32* %4, align 4
#    call void @warp_level_parallel_memcpy(i32 %7, i8* %8, i8* %9, i32 %10)
#    ret void
#}

region_copy.args[0].name = "block_id"
region_copy.args[1].name = "tid"
region_copy.args[2].name = "orig_copy"
region_copy.args[3].name = "size"
region_copy.args[4].name = "new_copy"
region_copy.args[5].name = "union_copy"

enblk = region_copy.append_basic_block("entry")

bldr = Builder.new(enblk)

a = bldr.alloca(intty)
a.alignment = 4
b = bldr.alloca(intty)
b.alignment = 4
c = bldr.alloca(charty)
c.alignment = 8
d = bldr.alloca(intty)
d.alignment = 4
e = bldr.alloca(charty)
e.alignment = 8
f = bldr.alloca(charty)
f.alignment = 8

arg0, arg1, arg2, arg3, arg4, arg5 = region_copy.args

a_store = bldr.store(arg0, a)
b_store = bldr.store(arg1, b)
c_store = bldr.store(arg2, c)
d_store = bldr.store(arg3, d)
e_store = bldr.store(arg4, e)
f_store = bldr.store(arg5, f)

load_b = bldr.load(b)
load_e = bldr.load(e)
load_c = bldr.load(c)
load_d = bldr.load(d)

bldr.call(warp_level_parallel_memcpy,[load_b, load_e, load_c, load_d])

bldr.ret_void()


warp_level_parallel_memcpy.args[0].name = "tid"
warp_level_parallel_memcpy.args[1].name = "dst"
warp_level_parallel_memcpy.args[2].name = "src"
warp_level_parallel_memcpy.args[3].name = "size"

enblk = warp_level_parallel_memcpy.append_basic_block("entry")
blk_15 = warp_level_parallel_memcpy.append_basic_block("blk_15")
blk_21 = warp_level_parallel_memcpy.append_basic_block("blk_21")
blk_29 = warp_level_parallel_memcpy.append_basic_block("blk_29")
blk_39 = warp_level_parallel_memcpy.append_basic_block("blk_39")
blk_40 = warp_level_parallel_memcpy.append_basic_block("blk_40")
blk_43 = warp_level_parallel_memcpy.append_basic_block("blk_43")

bldr = Builder.new(enblk)

intptrty = Type.pointer(Type.int(32))

a_w = bldr.alloca(intty)
a.alignment = 4
b_w = bldr.alloca(charty)
b_w.alignment = 8
c_w = bldr.alloca(charty)
c_w.alignment = 8
d_w = bldr.alloca(intty)
d_w.alignment = 4
e_w = bldr.alloca(intptrty)
e_w.alignment = 8
e_w.name = "opt_dst"
f_w = bldr.alloca(intptrty)
f_w.alignment = 8
f_w.name = "opt_src"
g_w = bldr.alloca(intty)
g_w.alignment = 4
g_w.name = "opt_size"
h_w = bldr.alloca(intty)
h_w.alignment = 4
h_w.name = "ttid"
i_w = bldr.alloca(intty)
i_w.alignment = 4
i_w.name = "k"
j_w = bldr.alloca(intty)
j_w.alignment = 4
j_w.name = "idx"

#define void @warp_level_parallel_memcpy(i32 %tid, i8* %dst, i8* %src, i32 %size) #0{
#    %1 = alloca i32, align 4
#    %2 = alloca i8*, align 8
#    %3 = alloca i8*, align 8
#    %4 = alloca i32, align 4
#    %opt_dst = alloca i32*, align 8
#    %opt_src = alloca i32*, align 8
#    %opt_size = alloca i32, align 4
#    %ttid = alloca i32, align 4
#    %k = alloca i32, align 4
#    %idx = alloca i32, align 4

arg0, arg1, arg2, arg3 = warp_level_parallel_memcpy.args

bldr.store(arg0, a_w)
bldr.store(arg1, b_w)
bldr.store(arg2, c_w)
bldr.store(arg3, d_w)

#    store i32 %tid, i32* %1, align 4
#    store i8* %dst, i8** %2, align 8
#    store i8* %src, i8** %3, align 8
#    store i32 %size, i32* %4, align 4

load_b = bldr.load(b_w)
load_b_c = bldr.bitcast(load_b, intptrty)
bldr.store(load_b_c, e_w)

#    %5 = load i8** %2, align 8
#    %6 = bitcast i8* %5 to i32*
#    store i32* %6, i32** %opt_dst, align 8

load_c = bldr.load(c_w)
load_c_c = bldr.bitcast(load_c, intptrty)
bldr.store(load_c_c, f_w)

#    %7 = load i8** %3, align 8
#    %8 = bitcast i8* %7 to i32*
#    store i32* %8, i32** %opt_src, align 8

load_d = bldr.load(d_w)
load_d_s = bldr.sext(load_d, int64ty)
load_d_s_d = bldr.udiv(load_d_s, Constant.int(int64ty, 4))
load_d_s_d_t = bldr.trunc(load_d_s_d, intty)
bldr.store(load_d_s_d_t, g_w)

#    %9 = load i32* %4, align 4
#    %10 = sext i32 %9 to i64
#    %11 = udiv i64 %10, 4
#    %12 = trunc i64 %11 to i32
#    store i32 %12, i32* %opt_size, align 4

load_a = bldr.load(a_w)
load_a_s = bldr.srem(load_a, Constant.int(intty, 16))
bldr.store(load_a_s, h_w)
bldr.store(Constant.int(intty, 0), i_w)
bldr.branch(blk_15)

#    %13 = load i32* %1, align 4
#    %14 = srem i32 %13, 16
#    store i32 %14, i32* %ttid, align 4
#    store i32 0, i32* %k, align 4
#    br label %15

bldr.position_at_end(blk_15)

load_i = bldr.load(i_w)
load_g = bldr.load(g_w)
d_g_i = bldr.sdiv(load_g, Constant.int(intty, 16))
d_g_i_1 = bldr.add(d_g_i, Constant.int(intty, 1), nsw = True)
cmp_result = bldr.icmp( ICMP_SLT , load_i, d_g_i_1)
bldr.cbranch(cmp_result, blk_21, blk_43)

#; <label>:15                    ; preds = %40, %0
#    %16 = load i32* %k, align 4
#    %17 = load i32* %opt_size, align 4
#    %18 = sdiv i32 %17, 16
#    %19 = add nsw i32 %18, 1
#    %20 = icmp slt i32 %16, %19
#    br i1 %20, label %21, label %43

bldr.position_at_end(blk_21)

load_h = bldr.load(h_w)
load_i = bldr.load(i_w)
h_i_m = bldr.mul(Constant.int(intty, 16), load_i, nsw = True)
h_m_a = bldr.add(load_h, h_i_m, nsw = True)
bldr.store(h_m_a, j_w)
load_j = bldr.load(j_w)
load_g = bldr.load(g_w)
cmp_result = bldr.icmp(ICMP_SLT, load_j, load_g)
bldr.cbranch(cmp_result, blk_29, blk_39)

# ; <label>:21                               ; preds = %15
#    %22 = load i32* %ttid, align 4
#    %23 = load i32* %k, align 4
#    %24 = mul nsw i32 16, %23
#    %25 = add nsw i32 %22, %24
#    store i32 %25, i32* %idx, align 4
#    %26 = load i32* %idx, align 4
#    %27 = load i32* %opt_size, align 4
#    %28 = icmp slt i32 %26, %27
#    br i1 %28, label %29, label %39

bldr.position_at_end(blk_29)

load_j = bldr.load(j_w)
load_j_s = bldr.sext(load_j, int64ty)
load_f = bldr.load(f_w)
array_elm = bldr.load(bldr.gep(load_f,[load_j_s]))
load_j = bldr.load(j_w)
load_j_s = bldr.sext(load_j, int64ty)
load_e = bldr.load(e_w)
array_elm2 = bldr.gep(load_e,[load_j_s])
bldr.store(array_elm, array_elm2)
bldr.branch(blk_39)

#; <label>:29                                 ; preds = %21
#   %30 = load i32* %idx, align 4
#   %31 = sext i32 %30 to i64
#   %32 = load i32** %opt_src, align 8
#   %33 = getelementptr inbounds i32* %32, i64 %31
#   %34 = load i32* %33, align 4
#   %35 = load i32* %idx, align 4
#   %36 = sext i32 %35 to i64
#   %37 = load i32** %opt_dst, align 8
#   %38 = getelementptr inbounds i32* %37, i64 %36
#   store i32 %34, i32* %38, align 4
#   br label %39

bldr.position_at_end(blk_39)

bldr.branch(blk_40)
# ; <label>:39                                      ; preds = %29, %21
#    br label %40

bldr.position_at_end(blk_40)

load_i = bldr.load(i_w)
i_a_1 = bldr.add(load_i, Constant.int(intty, 1))
bldr.store(i_a_1, i_w)
bldr.branch(blk_15)

# ; <label>:40                                      ; preds = %39
#    %41 = load i32* %k, align 4
#    %42 = add nsw i32 %41, 1
#    store i32 %42, i32* %k, align 4
#    br label %15

bldr.position_at_end(blk_43)

bldr.call(syncthreads,[])
bldr.ret_void()

#; <label>:43                                      ; preds = %15
#    call void @__syncthreads()
#        ret void
#}


#warp_level_parallel_memcpy.blocks

#ControlFlowGraph(warp_level_parallel_memcpy)

#print warp_level_parallel_memcpy.verify()

print mod

with open('gpuRaceDetection.ll', 'w') as f:
    f.write(mod.__str__())


