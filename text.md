

Tutorial for Iterating Over a Python List
===============

Dong Chen

Introduction
------------

A Python list is an ordered sequence of items which don’t have to be of the same type. Numbers, letters, strings, nested lists can on the same list.

<b>List creation:</b>

The plain way to create a Python list is just by statically writing the items between square brackets.

```python
	list ＝ ［ 1，‘a’， “hello”， sublist， Student(“Dong”) ］
```

List can also be created by list comprehensions. List comprehension is a description about what list should be created. It contains two parts: one is what the items in the list will be like, the other is how to get them.
```python
	list = [ x+y for x in ‘one’ for y in ’two’]
	>>> list
	>>> [‘ot’,’ow’,’oo’,’nt’,’nw’,’no’,’et’,’ew’,’eo’]
```
<b>Iterating over a Python list:</b>

<i>for-in</i> statement in Python can easily perform list iterating.
```python
	list = [1, 2, 3, 4]
	for item in list:
  		print (item)

  	>>>1
  	2
  	3
  	4
```
Assemble Code
------------

<b>Python Code:</b>
```python
	list = [1, 2, 3, 4]
	for item in list:
  		print (item)
```
<b>Assemble Code:</b>
Then we can compile Python code to Python Bytecode and display the disassembled Bytecode by command line:

	python -m dis filename.py

The resulting assemble code is listed below:
```python
	1         0 LOAD_CONST               0 (1)
              3 LOAD_CONST               1 (2)
              6 LOAD_CONST               2 (3)
              9 LOAD_CONST               3 (4)
             12 BUILD_LIST               4
             15 STORE_NAME               0 (list)

	 2       18 SETUP_LOOP              19 (to 40)
             21 LOAD_NAME                0 (list)
             24 GET_ITER
        >>   25 FOR_ITER                11 (to 39)
             28 STORE_NAME               1 (item)

    3        31 LOAD_NAME                1 (item)
             34 PRINT_ITEM
             35 PRINT_NEWLINE
             36 JUMP_ABSOLUTE           25
        >>   39 POP_BLOCK
        >>   40 LOAD_CONST               4 (None)
             43 RETURN_VALUE
```
Execution Framework
------------
The execution process of iterating the list can be visualized on <a http://pythontutor.com/">Python Tutorial</a>. Python frame will first create a list contains 4 items and push the list to the execution stack. Then iterator will return items one by one each time when <i>FOR_ITER</i> is executed. The frame will push the item into stack and <i>PRINT_ITEM</i> will pop the item out and display it on screen.

![Alt text](./1.png)

![Alt text](./2.png)

By given a Python code, it will first be compiled to Python Bytecode. Then the interpreter of Python will execute the Python Bytecode. The framework of Python interpreter is listed below. First, the frame will load the code into PyCodeObject <i>co</i>. Then the pointer <i>first_isntr</i> is pointed to the start address of the code. The address of the next instruction is calculated and stored into <i>next_instr</i>. Finally, offset is updated, instruction is got out to <i>opcode</i> and the pointer <i>next_instr</i> is increased by one. Now the <i>opcode</i> can be executed by one of the branches of <i>switch</i>.
```c
		...
		co = f->f_code;
		first_instr = (unsigned char*)
		PyString_AS_STRING(co->co_code);
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
```


We can see in the <i>switch</i> statements, there are a lot of <i>PREDICT()</i>, <i>PREDICTED()</i> and <i>PREDITED_WITH_ARG()</i> macros are defined. These macros are used in pairs. <i>PREDICT()</i> will guess the next operation, if the next operation is <i>op</i>, it means that the prediction is successful and can directly jump to the <i>PREDICTED()</i> or <i>PREDITED_WITH_ARG()</i> which actually defines the label.

```c
	#define PREDICT(op)	  if (*next_instr == op) goto PRED_##op
	#define PREDICTED(op)           PRED_##op: next_instr++
	#define PREDICTED_WITH_ARG(op)  PRED_##op: oparg = PEEKARG(); next_instr += 3
```

Python Bytecode for Iterating
----------

There are four Python Bytecodes that implemented the iterating function of Python: SETUP_LOOP, GET_ITER, FOR_ITER and JUMP_ABSOLUTE.

<b>SETUP_LOOP</b>
```c
	case SETUP_LOOP:
	case SETUP_EXCEPT:
    case SETUP_FINALLY:
    	PyFrame_BlockSetup(f, opcode, INSTR_OFFSET() + oparg, STACK_LEVEL());
    continue;
```
SETUP_LOOP is to create a basic block which contains the body of the loop. It will create a block object which maintains the exit address of the next instruction should be executed when the block pop out of the block stack. <i>INSTR_OFFSET() + oparg</i> calculates the exit address. <i>opcode</i> is the value of macro SETUP_LOOP, SETUP_EXCEPT or SETUP_FINALLY which will be recorded by the Python block object.

<b>GET_ITER</b>
```c
	case GET_ITER:
		v = TOP();
		x = PyObject_GetIter(v);
		Py_DECREF(v);
        if (x != NULL) {
        	SET_TOP(x);
            PREDICT(FOR_ITER);
            continue;
        }
        STACKADJ(-1);
        break;
```
GET_ITER is to get the iterator object for whatever object on the top of the execution stack. If the top object does not have an iterator object, the top object will be popped out of the stack. Else <i>PyObject_GetIter()</i> will return the iterator. The function which can return the iterators are implemented in Python type object, each Python type has its own iterator method whose entrance can be found by <i>t->tp_iter</i>.
```c
	PyObject * PyObject_GetIter(PyObject *o) {
		PyTypeObject *t = o->ob_type;
		f = t->tp_iter;
		PyObject *res = (*f)(o);   /* list_iter() */
		return res;
	}
```
For Python list object, based on the definition of PyList_Type the function entrance got by <i>t->tp_iter</i> is <i>list_iter</i>. <i>list_iter<\i> will create a list iterator object which contains both the index and pointer to the original list object.
```c
	PyTypeObject PyList_Type = {
    ...
    list_iter,                                  /* tp_iter */
    0,                                          /* tp_iternext */
    list_methods,                               /* tp_methods */
    ...
	};

	static PyObject * list_iter(PyObject *seq)
	{
    	listiterobject *it;

    	if (!PyList_Check(seq)) {
        	PyErr_BadInternalCall();
        	return NULL;
    	}
    	it = PyObject_GC_New(listiterobject, &PyListIter_Type);
    	if (it == NULL)
        	return NULL;
    	it->it_index = 0;
    	Py_INCREF(seq);
    	it->it_seq = (PyListObject *)seq;
    	_PyObject_GC_TRACK(it);
    	return (PyObject *)it;
	}
```
<b>FOR_ITER</b>

```c
	case FOR_ITER:
		v = TOP();
		x = (*v->ob_type->tp_iternext)(v);
			if (x != NULL) {
				PUSH(x);
				PREDICT(STORE_FAST);
				PREDICT(UNPACK_SEQUENCE);
				continue;
			}
			if (PyErr_Occurred()) {
				if (!PyErr_ExceptionMatches(PyExc_StopIteration))
                    break;
                PyErr_Clear();
            }
		x = v = POP();
        Py_DECREF(v);
        JUMPBY(oparg);
        continue;
```

FOR_ITER is actually to let the iterator return the next object and push it into stack. If iterator has reached the end, NULL will be returned. Then the iterator object will be popped out and jump to the operation with address of next operation add an offset <i>oparg</i> which will exit the iteration. The way to get the entrance to the next method of iterators works the same way as getting the entrance of the function which returns the iterator. The next method are implemented in the Python type object and the entrance of the next method can be get by <i>type->tp_iternext</i>.

```c
 	PyTypeObject PyListIter_Type = {
		...
   		PyObject_SelfIter,                          /* tp_iter */
    	(iternextfunc)listiter_next,                /* tp_iternext */
    	listiter_methods,                           /* tp_methods */
    	...
    };
```

For Python list object, the <i>tp_iternext</i> method is <i>listiter_next</i>. It will return the item in list with index <i>it_index</i> and increase the index. If the index equals to the length of the list size, it means the iterator has reached the end and NULL will be returned.

```c
	listiter_next(listiterobject *it)
	{
    	PyListObject *seq;
    	PyObject *item;

    	assert(it != NULL);
    	seq = it->it_seq;
    	if (seq == NULL)
        	return NULL;
    	assert(PyList_Check(seq));

    	if (it->it_index < PyList_GET_SIZE(seq)) {
        	item = PyList_GET_ITEM(seq, it->it_index);
        	++it->it_index;
        	Py_INCREF(item);
        	return item;
    	}

    	Py_DECREF(seq);
    	it->it_seq = NULL;
    	return NULL;
	}
```