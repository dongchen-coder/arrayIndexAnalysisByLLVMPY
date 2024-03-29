
Tutorial for Iterating Over a Python List
===============

Dong Chen

Introduction
------------

<big>A Python list is an ordered sequence of items which don’t have to be of the same type. Numbers, letters, strings, nested lists can on the same list.

For example:
 
	list ＝ ［ 1，‘a’， “hello”， sublist， Student(“Dong”) ］

	list = [ x+y for x in ‘one’ for y in ’two’]

  	
Python Bytecode for Iterating
------------

Python code will first be compiled to Python Bytecode. Then the interpreter of Python will execute the Python Bytecode. 

<b>Python Code:</b>
	
	list = [1, 2, 3, 4]
	for item in list:
  		print (item)

<b>Disassembled Code:</b>   
Then we can compile Python code to Python Bytecode and display the disassembled Bytecode.

	//cmdline: python -m dis filename.py
  	1         0 LOAD_CONST        0 (1)
              3 LOAD_CONST        1 (2)
              6 LOAD_CONST        2 (3)
              9 LOAD_CONST        3 (4)        // load 4 integer objects into stack
             12 BUILD_LIST        4            // pop 4 ojbects out from stack and build a list object
             15 STORE_NAME        0 (list)      

 	2        18 SETUP_LOOP        19 (to 40)
             21 LOAD_NAME         0 (list)
             24 GET_ITER                       // push the list iterator object to stack
        >>   25 FOR_ITER          11 (to 39)   // begin iterating
             28 STORE_NAME        1 (item)

  	3        31 LOAD_NAME         1 (item)
             34 PRINT_ITEM                     // display the TOS object
             35 PRINT_NEWLINE                  // start a new line
             36 JUMP_ABSOLUTE     25           // jump to FOR_ITER
        >>   39 POP_BLOCK           
        >>   40 LOAD_CONST        4 (None)
             43 RETURN_VALUE

Execution Framework
------------
The execution process of iterating the list can be visualized on <a http://pythontutor.com/">Python Tutorial</a>. The framework of Python interpreter is listed below. First, the frame will load the code into PyCodeObject <i>co</i>. Then the pointer <i>first_isntr</i> is pointed to the start address of the code. The address of the next instruction is calculated and stored into <i>next_instr</i>. Finally, offset is updated, instruction is got out to <i>opcode</i> and the pointer <i>next_instr</i> is increased by one. Now the <i>opcode</i> can be executed by one of the branches of <i>switch</i>.

	//ceval.c
	...
	co = f->f_code;
	first_instr = (unsigned char*) PyString_AS_STRING(co->co_code);
 	next_instr = first_instr + f->f_lasti + 1;
	for (;;) {
		f->f_lasti = INSTR_OFFSET(); /*f->f_lasti = next_instr - first_instr */
		opcode = *next_instr++;
	
		switch (opcode) {
			case (LOAD_CONST): ... continue;
			
			case (...): ... break;
			
			case (GET_ITER): ...PREDICT(FOR_ITER); continue;
	
			PREDICTED_WITH_ARG(FOR_ITER);
			case (FOR_ITER): ... continue;
	
			...
		}
	}

We can see in the <i>switch</i> statements, there are a lot of <i>PREDICT()</i>, <i>PREDICTED()</i> and <i>PREDITED_WITH_ARG()</i> macros are defined. These macros are used in pairs. <i>PREDICT()</i> will guess the next operation, if the next operation is <i>op</i>, it means that the prediction is successful and can directly jump to the <i>PREDICTED()</i> or <i>PREDITED_WITH_ARG()</i> which actually defines the label. 

	//ceval.c
	#define PREDICT(op)	  if (*next_instr == op) goto PRED_##op
	#define PREDICTED(op)           PRED_##op: next_instr++
	#define PREDICTED_WITH_ARG(op)  PRED_##op: oparg = PEEKARG(); next_instr += 3

Diving into Python Bytecode
---------- 

There are four Python Bytecodes that implemented the iterating function of Python: SETUP_LOOP, GET_ITER, FOR_ITER and JUMP_ABSOLUTE. SETUP_LOOP and GET_ITER will actually do the initialization for looping and FOR_ITER and JUMP_ABSOLUTE will do the looping. We will walk through all the four key Bytecode by tracing iterating over list [1,2,3,4]. 

Before the list iteration, a new block which contains the body of the loop will be created. It  maintains the block type and the exit address of the next instruction should be executed when the block pop out of the block stack. <i>opcode</i> is the value of macro SETUP_LOOP, SETUP_EXCEPT or SETUP_FINALLY which will be recorded by the Python block object to define the type which will tell why the block is created. <i>INSTR_OFFSET() + oparg</i> calculates the exit address. In this case the <i>INSTR_OFFSET()</i> is 28 and <i>oparg</i> held by SETUP_LOOP is 11, the result is 39 which is the address of POP_BLOCK.

	//ceval.c
	case SETUP_LOOP:
	case SETUP_EXCEPT:
    case SETUP_FINALLY:
    	PyFrame_BlockSetup(f, opcode, INSTR_OFFSET() + oparg, STACK_LEVEL());
    continue;

After a new block for loop is built, list [1,2,3,4] will be load to the top of execution stack. GET_ITER will get the iterator object for whatever object on the top of the execution stack. If the top object does not have an iterator object, the top object will be popped out of the stack. Else <i>PyObject_GetIter()</i> will return the iterator. The function which can return the iterators are implemented in Python type object, each Python type has its own iterator method whose entrance can be found by <i>t->tp_iter</i>.

	//ceval.c                     |  //abstract.c
	case GET_ITER:                |  PyObject * PyObject_GetIter(PyObject *o) {
		v = TOP();                |  	PyTypeObject *t = o->ob_type; 
		x = PyObject_GetIter(v);  |     f = t->tp_iter;
		SET_TOP(x);               |     PyObject *res = (*f)(o);
		continue;                 |     return res; }
        
In this case, v is the list object we created for [1,2,3,4]. <i>PyTypeObject</i> will be PyList_Type which defines all the methods and attributes for a Python list. Then we get the entrance of get iterator method by predefined <i>tp_iter</i>. By PyTypeObject's definition, the <i>tp_iter</i> will <i>be list_iter</i> which is the implementation to get list iterator. 

	//listobject.c
	PyTypeObject PyList_Type = {
    ...
    list_iter,                                  /* tp_iter */
    0,                                          /* tp_iternext */
    list_methods,                               /* tp_methods */
    ...}; 
 
By hiding the details of the errors checking part and reference count part of the code, the <i>list_iter()</i> function is listed below. <i>list_iter()</i> contains three steps to initialze the list iterator. First, it will try malloc space with garbage collector head. Second, it will initialize the index of the iterator to 0 which points to the first item 1 in list [1,2,3,4]. Third, it will point <i>it_seq</i> to list [1,2,3,4]. 

	//listobject.c
	static PyObject * list_iter(PyObject *seq)
	{
    	listiterobject *it;
    	it = PyObject_GC_New(listiterobject, &PyListIter_Type);
    	it->it_index = 0;
    	it->it_seq = (PyListObject *)seq;
    	return (PyObject *)it;
	}

When list iterator is initialized, FOR_ITER will be called to get the item out of the list by the index it held. So 1, 2, 3, 4 will be pushed into execution stack, each time FOR_ITER is called. What will happen by the fifth call? It will failed to get the none existing item, pop the iterator out and jump to the instruction whose offset is specified by <i>oparg</i>. Here, <i>oparg</i> is 11 and POP_BLOCK will be jumped to which means the iteration is over.  

	//ceval.c      
	//successfully get next item            | // failed to get next item             
	case FOR_ITER:                          | case FOR_ITER   
		v = TOP();                          | v = TOP();
		x = (*v->ob_type->tp_iternext)(v);  | x = (*v->ob_type->tp_iternext)(v);    
		PUSH(x);                            | x = v = POP();  JUMPBY(oparg);
		continue;                           | continue;

The way to get the entrance to the next method of iterators works the same way as getting the entrance of the function which returns the iterator. The next method are implemented in the Python type object and the entrance of the next method can be get by <i>type->tp_iternext</i>. By definiation of <i>PyListIter_Type</i>, <i>tp_iternext</i> methods is implemented as <i>listiter_next()</i> in listobject.c. During the first four runs, <i>it_index</i> in  <i>listiter_next()</i> will be 0,1,2,3 which is smaller than the list size 4. So the item will be got out and index will increase by one. When the fifth call happens, <i>it_index</i> is 4 which does not satisfy the condition. So the pointer <i>it_seq</i> which points to list [1,2,3,4] will be set to NULL and NULL will be returned to tell the interpreter the iterator has reached the end.
	
	//listobject.c
	listiter_next(listiterobject *it)
	{
    	...//initialize
    	if (it->it_index < PyList_GET_SIZE(seq)) {
        	item = PyList_GET_ITEM(seq, it->it_index);
        	++it->it_index;
        	return item;
    	}
    	it->it_seq = NULL;
    	return NULL;
	}

</big>