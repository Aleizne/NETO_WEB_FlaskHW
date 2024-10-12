from datetime import datetime
import flask
from flask import request
import pydantic
import sqlite3
import uuid

app = flask.Flask('app')

# за алхимию инквизиция недовольна(
connection = sqlite3.connect('AdvDB.db')
cursor = connection.cursor()

table_1 = """create table if not exists User(
    user_id text not null unique primary key,
    name text not null,
    password text not null,
    email text not null unique
);
"""
table_2 = """create table if not exists Advertise(
    adv_id text not null unique primary key,
    header text not null,
    discrpt text not null,
    created_at text not null,
    owner_id text not null
);
"""
cursor.execute(table_1)
cursor.execute(table_2)
connection.commit()


# слой данных
class User(pydantic.BaseModel):
    user_id: str = pydantic.Field(default_factory=uuid.uuid4)
    name: str
    password: str
    email: str


class Advertise(pydantic.BaseModel):
    adv_id: str = pydantic.Field(default_factory=uuid.uuid4)
    header: str
    discrpt: str
    created_at: datetime = pydantic.Field(default_factory=datetime.now)
    owner_id: str


# бизнес логика
def add_adv(header, discrpt, owner_id):
    add_script = """insert into Advertise values
    (?, ?, ?, ?, ?); 
    """
    advertise = Advertise(header=header,
                          discrpt=discrpt,
                          owner_id=owner_id)
    execute_script(add_script, str(advertise.adv_id), advertise.header,
                   advertise.discrpt, str(advertise.created_at), advertise.owner_id)
    return str(advertise.adv_id)


def get_adv(adv_id):
    select_script = """select adv_id, header, discrpt, created_at, owner_id
    from Advertise
    where adv_id = ?
    """
    data = execute_script(select_script, adv_id)
    if data is None:
        return None
    res = Advertise(adv_id=data[0],
                    header=data[1],
                    discrpt=data[2],
                    created_at=datetime.strptime(data[3], "%Y-%m-%d %H:%M:%S.%f"),
                    owner_id=data[4])
    return res.dict()


def update_adv(adv_id, data):
    current_data = get_adv(adv_id)
    if current_data is None:
        return
    current_data = {**current_data, **data}
    update_script = """update Advertise
    set header = ?,
    discrpt = ?
    where adv_id = ?
    """
    execute_script(update_script,
                   current_data['header'],
                   current_data['discrpt'],
                   adv_id)


def delete_adv(adv_id):
    del_script = """delete from Advertise
    where adv_id = ?;
    """
    execute_script(del_script, adv_id)


# DAO - слой
def execute_script(script: str, *args):
    connect = sqlite3.connect('AdvDB.db')
    cur = connect.cursor()
    cur.execute(script, args)
    res = cur.fetchone()
    connect.commit()
    return res


# app - слой
@app.route('/get/<string:adv_id>', methods=['GET'])
def get_post(adv_id):
    return get_adv(adv_id) or {}


@app.route('/delete/<string:adv_id>', methods=['DELETE'])
def delete_post(adv_id):
    return delete_adv(adv_id)


@app.route('/add/', methods=['POST'])
def add_post():
    data = request.json
    res = add_adv(header=data['header'],
                  discrpt=data['discrpt'],
                  owner_id=data['owner_id'])
    return dict(adv_id=res)


@app.route('/put/', methods=['PUT'])
def update_post():
    data = request.json
    update_adv(adv_id=data['adv_id'], data=data)


if __name__ == '__main__':
    app.run()
