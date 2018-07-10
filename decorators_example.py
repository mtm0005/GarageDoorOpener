
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