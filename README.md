# Equation-Solver-and-Parser
Equation solver and parser

This little programm can be used to solve systems of (in)equations with the help of z3.

It can parse the text of your input and transform it into the language of z3.
z3 will find a solution and returns exactly one, if there is one.
The solution can be tested with a function called pytest_helper if you don't believe the answer is correct.

Have a look at PStA.py line 125 and ongoing. There are a lot of examples that demonstrate what this programm can do. 
The commented lines at the beginning of some functions are for pytest. You can see there what output the code would generate.
