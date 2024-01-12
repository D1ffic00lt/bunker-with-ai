import sqlalchemy.ext.declarative as dec

from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker, AsyncSession
from typing import Union, Callable

__factory: Union[Callable, None] = None
SqlAlchemyBase = dec.declarative_base()


async def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("no db file name")

    conn_str = f'sqlite+aiosqlite:///{db_file.strip()}?check_same_thread=False'

    engine = create_async_engine(conn_str, echo=False)
    __factory = async_sessionmaker(engine)

    try:
        from . import __all_models
    except ImportError:
        pass

    async with engine.begin() as conn:
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)


def create_session() -> AsyncSession:
    global __factory
    return __factory()