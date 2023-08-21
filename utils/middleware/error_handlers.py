def message_error_handler(f):
    async def wrapper(*args, **kwargs):
        print(kwargs)

        r = await f(*args, **kwargs)

        return r
    return wrapper
