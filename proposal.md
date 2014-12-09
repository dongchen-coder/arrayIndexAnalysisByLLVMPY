<big>
Post 1

CSC 453: Code transformations for GPU race detection with llvm-py
=======

Dong Chen

Introduction
-----------


Code transformations are widely used in performance concerned optimizations, programming productivity and so on. LLVM infrastructure is often used. But C++ abased interface is hard to be used during the development. Here we use LLVM-py interface to do code transformations for GPU race detection.

Architecture and execution model of GPU
---------------------------------------

The hardware structure of GPU consists of two major parts: processing part and hierarchical memory part. The processing part is referred as streaming multiprocessors(SM). Each GPU contains a number of SMs and each SM contains an array of streaming processors(SP). The hierarchical memory has three levels: device memory, shared memory and private memory. Device memory can be accessed by all the SPs in every SMs. Each SM has its own shared memory which can be accessed by all the SPs belong to the SM. Each SP has it own private memory which can only be access by itself.

GPU programs contain two parts: the main program and the kernel program. The main program will do initialization, copy data from main memory to device memory, launch kernel program on GPU and copy data back from device memory to main memory once the kernel program finished running. Kernel program will be mapped into thousands of threads. And threads are organized in thread blocks. Thread blocks will be assigned to each SM to execute and threads in the same thread block will be executed on the array of SPs in warps.

So threads in GPU can share data on shared memory and device memory. Data races will occur if synchronization is not correctly used. But current compiler can not detect races.

![Alt text](./4.png)

GPU Races detection by two-pass run
----------------------------------

Our approach is to detect GPU races by transforming the kernel program and run it on GPU. Two runs are needed: one is to detect write-write races and the other is to detect write-read races. In the first run, we first copy the shared data for each warp and run the threads on their private copies. Then compare the result, if the write regions are not overlapping, it means no write-write races. Else write-write races will happen. The second pass will use the result of the first run as the initial state. Then run and compare, if different, write-read race will happen.

![Alt text](./3.png)


Code transformations needed
---------------------------

1. iterating through AST and replacing variables

 	* instructions for declaring new variables

			int a;         --->     int a[M]
			int a[N]; 	   --->     int a[M][N]

  	* instructions for access redirection
  	
  			a              --->      a[warpID] 
  			a[i]           --->      a[warpID][i]        

2.  inserting functions to do memory copy, memory compare
	
	* 
	
			region_copy();
			union_copy();
			region_diff();


Update Post 2
------------

llvmpy can be easily used to generate LLVM IR code, so inserting LLVM IR code of the functions is a good choice. The first step is to generate the functions which will be called by kernels for race detection. Let's take <i>region_copy()</i> as an example, the original C code of <i>region_copy()</i> is listed below, it will copy the data from <i>orig_src</i> to <i>new_copy</i> in parallel:
		
		void warp_level_parallel_memcpy( int tid,
                       char * dst, char * src, int size)
		{
   			int * opt_dst = (int *) dst ;
    		int * opt_src = (int *) src ;
    		int opt_size  = size / sizeof(int) ;

    		int ttid = tid % WARP_SIZE;
    		for (int k=0; k< (opt_size / WARP_SIZE)+1; k ++ ) {
        		int idx = ttid + WARP_SIZE * k ;
        		if ( idx < opt_size )
           			opt_dst[idx] = opt_src[idx] ;
    		}
    		__syncthreads() ;
		}

		void region_copy( int block_id, int tid, char * orig_copy, int size,
                     char * new_copy, char * union_copy)
		{
    		warp_level_parallel_memcpy( tid, new_copy, orig_copy, size ) ;
		}

Writing the above functions in llvmpy is quite straight forward, but should be in the form of LLVM IR. In LLVM IR, functions are contained in modules. Each function should contain at least one "entry" basic block. The instructions are inserted to each basic block of the function in order.

The skeleton is listed below. 

1. Define data types and function types. llvmpy provides Type object to define the data types and function types. 
		
		#define "int" type
		intty = Type.int(32)
		
		#define "char *" type 
		charty = Type.pointer(Type.int(8))
		
		#define function type which is "void FUNCTION(int, int, char *, int, char *, char *)"
		fnty = Type.function(Type.void(), [intty, intty, charty, intty, charty, charty])
			
3. Define a function based on one function type
		
		region_copy = Function.new(mod, fnty, name='region_copy')
	
4. Setting the arguments. In llvmpy, the arguments of one function can be return just by assignment. And the attributes of each argument can be easily modified.
		
	
		arg0, arg1, arg2, arg3, arg4, arg5 = region_copy.args
		region_copy.args[0].name = "block_id"
	
5. Define basic block in one function and inserting instructions
			
		#inserting basic block
		enblk = region_copy.append_basic_block("entry")
		
		#inserting instructions
		a = bldr.alloca(intty)    # %0 = alloca i32, align 4
		a.alignment = 4
		a_store = bldr.store(arg0, a) # store i32 %block_id, i32* %0
		
		#inserting instruction for function call
		bldr.call(warp_level_parallel_memcpy,[load_b, load_e, load_c, load_d])

<b>Summary:</b>

What can be done for now(easiest):

All the functions which will be used in the GPU Race detection can be generated. The llvmpy code is listed <a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/gpuRaceDetection.py">here</a>.
The generated code is listed <a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/gpuRaceDetection.ll">here</a>.

What should be done next(sort from easy to hard):

1. Find the way to analysis the code, which means find whether there is way to iterating over the code.
2. Find the way to insert instructions, such as function calls, new variables, and so on.
3. Find the way to replace variables in instructions.

But for now, whether llvmpy supports analysis is still need to be explored. Pass manager part of llvmpy should be further checked.

Update Post 3
------------

Answering previous questions:

1. Find the way to analysis the code, which means find whether there is way to iterating over the code.

	llvmpy provides a very convenient way to analysis the LLVM IR code, so LLVM IR level analysis can be easily performed.

		for f in mod.functions:
    		for bb in f.basic_blocks:
        		for istr in bb.instructions:
            		for operand in istr.operands:

2.  Find the way to insert instructions, such as function calls, new variables, and so on.

	llvmpy provides a set of API which can modify LLVM IR: inserting functions to mudule, inserting basic blocks to functions, inserting instructions to basic blocks.
	
		#add function fo module
			module.add_function() 
		#insert basic block before the current basic block
			basic_block.insert_before() 
		#insert 'add' instruction before instruction 'cinst'
			Builder.position_before(cinst)
			Builder.add()		

3. Find the way to replace variables in instructions.

	llvmpy provides an API to delete instructions from basic block, which can be replaced by a new instruction

		#delete instructions form basic block
		instruction.erase_from_parent()

<b>Summary</b>

But all the analysis and code transformation are performed in LLVM IR level, which is not convenient for source to source code transformation which is easier to be performed in AST level.	Python is a very good choice to implement the whole compiler, we can write a CUDA compiler to get the AST of CUDA program. (<a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/kaleidoscope.py">kaleidoscope</a>) provides a good example and reference. We can implement the following part one by one and generate AST ourself.

		1.tokenizer
		2.lexer
		3.paser (AST can be generated here)	
		4.code generator

What job is LLVMPY suitable to do:
----------------
	
<b>Array Access Analysis of GPU kernel program:</b>

<b><i>Why to perform Array Access Analysis?</i></b>

During execution, GPU kernel program will be mapped into thousands of threads. threads are grouped into thread blocks. The execution model requires that each thread blocks should be independent. That is to say there should be no data dependence. Without data dependence, thread blocks can be assigned to different GPUs and be executed by multiple GPUs at the same time. The speedup is almost linear. And with the knowledge of the exact array access range of each thread blocks, the assginment can be done automatically without explicit memory copy (host_to_device and device_to_host).

<b><i>Why program by LLVMPY is easier than using the origianl APIs?</i></b>

Compare the coding segments with same functionality between LLVM API and LLVMPY. LLVMPY has three advantages expecially when the application has a lot of codes:
	
1. Do not need to specify which iterator to use
2. No template functions which have to specify the type
3. No pointers

This makes implementation in LLVMPY much easier than in C++ LLVM API

```
// Original C++ LLVM API
for (Function::iterator b = F.begin(), be = F.end(); b != be; ++b) {
        for (BasicBlock::iterator i = b->begin(), ie = b->end(); i != ie; ++i) {
          if (CallInst* callInst = dyn_cast<CallInst>(&*i)) {
                       if (callInst->getCalledFunction() == targetFunc)
              ++callCounter;
          }
        }
      }
```
```
# llvmpy
for bb in f.basic_blocks:	for istr in bb.instructions:		if istr.opcode == OPCODE_CALL:			if its.operands[0] == targetFunc:
				callCounter=callCounter+1	
```

<b><i>Implementation:</i></b>

The impementation of array access analysis contains three parts: array index analysis, induction variables analysis and constains analysis.

array index analysis: (<a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/arrayAccessAnalysis.py">source code</a>)
	
* locating array access instruction ‘getelementptr’* construct prefix expression by define-use chains
* construct infix expresion from prefix expression

induction variables analysis:

* locating store to induction variable instructions* construct expression

constrains analysis:

* locating the basic blocks contain array access* construct Execution Path Tree from control flow graph* extract branch conditions to constrains



<b><i>Test: Matrix multiply</b></i>

GPU kernel program of matrix multiply (<a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/matrixMul.c">C</a>, <a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/matrixMul.ll">LLVM IR</a>) 

Array index analysis result:

	A = a + wA * ty + tx
	B = b + wB * ty + tx
	C = wB * 32 * by + 32 * bx + wB * ty + tx

With knowledge of a and b are induction variables and following the following rules:

	a = ( wA * 32 * by : 32 : wA * 32 * by + wA - 1 ) (additional induction variable analysis)
	b = ( 32 * bx : 32 * wB : 32 * bx + wB - 1 ) (additional induction variable analysis) 
	tx = ( 0 : 1 : 31) (runtime)
	ty = ( 0 : 1 : 31) (runtime)
	
Exact access range by threads block can be calculated with its IDs (bx, by).

<a href="https://github.com/dongchen-coder/dongchen-coder.github.io/blob/master/final_report.pdf">presentation (PPT)</a>

</big>