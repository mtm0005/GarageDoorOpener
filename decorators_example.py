
def say_hello(func):
    def func_wrapper(*args, **kwargs):
        print('hello')
        result = func(*args, **kwargs)
        print('goodbye')
        return result
    return func_wrapper

@say_hello
def foo(x):
    print('foo bar {}'.format(x))
    return x

b = foo(5)
print(b)

def try_thrice(func):

    def func_wrapper(*args, **kwargs):
        num_tries = 0
        while True:
            try:
                print('trying func: {}'.format(num_tries))
                num_tries += 1
                result = func(*args, **kwargs)
                break
            except BaseException:
                if num_tries < 3:
                    continue
                else:
                    raise
        return result
    return func_wrapper

@try_thrice
def bad_func(x):
    return 5/x

nine = bad_func(9)
#zero = bad_func(0)

def try_it(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return None
    return func_wrapper

@try_it
def another_bad_func(x):
    return 8/x

s = another_bad_func(8)
q = another_bad_func(0)
print('{}, {}'.format(s, q))

def greeting(expr):
    def greeting_decorator(func):
        def function_wrapper(*args, **kwargs):
            print(expr + ", " + func.__name__ + " returns:")
            func(*args, **kwargs)
        return function_wrapper
    return greeting_decorator

@greeting("καλημερα")
def foo(x):
    print(42)

foo("Hi")

import multiprocessing
def log_error(msg, data):
    print('{} - {}'.format(msg, data))

def timeout(seconds=10):
    def timeout_decorator(func):
        def function_wrapper(*args, **kwargs):
            # start up a process running the decorated function.
            p = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
            p.start()

            # Wait for specified amount of time or until process finishes.
            p.join(seconds)

            # If thread is still active log an error and stop the process.
            if p.is_alive():
                log_error('timeout', 'seconds: {}, func: {}'.format(seconds, func.__name__))
                p.terminate()
                p.join()
        return function_wrapper
    return timeout_decorator

@timeout(1)
def idfg(x):
    while True:
        pass

idfg("Hi")