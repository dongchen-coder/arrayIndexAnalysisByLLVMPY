CSC 453: Code transformations for GPU race detection with llvm-py
=======

Dong Chen

Introduction
-----------
<big>

Code transformations are widely used in performance concerned optimizations, programming productivity and so on. LLVM infrastructure is often used. But C++ abased interface is hard to be used during the development. Here we use LLVM-py interface to do code transformations for GPU race detection.

Architecture and execution model of GPU
---------------------------------------

The hardware structure of GPU consists of two major parts: processing part and hierarchical memory part. The processing part is referred as streaming multiprocessors(SM). Each GPU contains a number of SMs and each SM contains an array of streaming processors(SP). The hierarchical memory has three levels: device memory, shared memory and pravite memory. Device memory can be accessed by all the SPs in every SMs. Each SM has its own shared memory which can be accessed by all the SPs belong to the SM. Each SP has it own private memory which can only be access by itself.

GPU programs contain two parts: the main program and the kernel program. The main program will do initialization, copy data from main memory to device memory, launch kernel program on GPU and copy data back from device memory to main memory once the kernel program finished running. Kernel program will be mapped into thousands of threads. And threads are organized in thread blocks. Thread blocks will be assigned to each SM to execute and threads in the same thread block will be executed on the array of SPs in warps.

So threads in GPU can share data on shared memory and device memory. Data races will occur if synchronization is not correctly used. But current compiler can not detect races.

![Alt text](./4.png)

GPU Races detection by two-pass run
----------------------------------

Our approach is to detect GPU races by transforming the kernel program and run it on GPU. Two runs are needed: one is to detect write-write races and the other is to detect write-read races. In the first run, we first copy the shared data for each warp and run the threads on their private copies. Then compare the result, if the write regions are not overlaping, it means no write-write races. Else write-write races will happen. The second pass will use the result of the first run as the initial state. Then run and compare, if different, write-read race will happen.

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
	
	Update:
	llvmpy can be used easily to generate LLVM IR, so inserting LLVM IR code of the functions is a good choice. The orginal C code of region_copy() is listed below:
		
		void warp_level_parallel_memcpy( int tid,
                       char * dst, char * src, int size)
		{
   			int * opt_dst = (int *) dst ;
    		int * opt_src = (int *) src ;
    		int opt_size  = size / sizeof(int) ; // hope size is times of 4.

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

	Writing the above functions in llvmpy is quite straight forward. The skeleton is listed below:
		
	1. define a function type, which gives the types of return value and argments.
		
			fnty = Type.function(Type.void(), [intty, intty, charty, intty, charty, charty])	
	2. define a funtion based on one function type
		
			region_copy = Function.new(mod,fnty, name='region_copy')
	
	3. define the names of arguments
		
			arg0, arg1, arg2, arg3, arg4, arg5 = region_copy.args
			region_copy.args[0].name = "block_id"
	
	4. define basic block in one function and inserting instructions
			
			#inserting basic block
			enblk = region_copy.append_basic_block("entry")
			#inserting instruction for funciton call
			bldr.call(warp_level_parallel_memcpy,[load_b, load_e, load_c, load_d])



</big>