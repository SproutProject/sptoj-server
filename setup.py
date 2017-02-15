import config
import model


if __name__ == '__main__':
    model.drop_schemas(config.DB_URL)
    model.create_schemas(config.DB_URL)
