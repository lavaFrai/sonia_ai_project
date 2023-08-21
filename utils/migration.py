import peewee


def do_migration_for(db: peewee.Database):
    def wrapper(model):
        db.create_tables([model])
        return model

    return wrapper
