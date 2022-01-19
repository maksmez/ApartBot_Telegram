from vedis import Vedis
import config


def get_current_price(user_id_price):
    with Vedis(config.db_file) as db:
        try:
            return db[user_id_price].decode()
        except KeyError:
            return config.States.User_Cost.value


def set_user_price(user_id_price, value):
    with Vedis(config.db_file) as db:
        try:
            db[user_id_price] = value
            return True
        except:
            # тут желательно как-то обработать ситуацию
            return False
