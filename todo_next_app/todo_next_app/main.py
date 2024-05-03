from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select
from todo_next_app import settings
from typing import Annotated
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware



#create model
class Todo(SQLModel, table = True):
    id : int |None = Field(default=None , primary_key= True) #make it a primary key, database will create the value not user
    content : str = Field(index=True, min_length=2 , max_length=50)
    is_complete : bool = Field(default= False)


connection_string : str = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=True) 
#connect_args={"sslmode":"require"} -> for secure connection
#pool_recycle=300 -> by default make pool of 5 connection, if connection is more then 300 sec then it will reload or recycle


# 
def create_tables():
    SQLModel.metadata.create_all(engine)


# todo1 : Todo = Todo(content= "first task")
# todo2 : Todo = Todo(content= "2nd task")


# #session -> for every user/transaction their is a different session, but engine is only one

# session = Session(engine)

# #create todo in database
# session.add(todo1)
# session.add(todo2)
# print(f'Before Commit{todo1}')
# session.commit()
# session.refresh(todo1)
# print(f'After Commit{todo2}')
# session.close()


#dependency injection
def get_session():
    with Session(engine) as session:
        yield session #return session

#this function will open and ends automatically, it will automaticlly perform session.close()


#things which must be done before starting the app
@asynccontextmanager
async def lifespan(app:FastAPI):
    print('Creating Tables')
    create_tables()
    print('Tables created')
    yield


app : FastAPI = FastAPI(lifespan=lifespan, title= "Todo App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins = ["*"]
#     allow_credentials = True
#     allow_methods = ["*"]
#     allow_headers = ["*"]
# )

@app.get('/')
async def root():
    return {"message": "Welcome to my ToDo App"}


'''
response_model = Todo -> data model, whatever returned from Todo is validate
in post user will enter a data with todo datatype, 
dependency session -> lossely couple with the session, debuging is tough
we dont have to execute commit, end, close again and again for every function
'''
@app.post('/todos/', response_model=Todo)
async def create_todo (todo: Todo, session:Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo
    #... this means that we will add the functionality later and it will not any error

@app.get('/todos/', response_model=list[Todo])
async def get_all(session:Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    if todos:
        return todos
    else:
        raise HTTPException(status_code=404, detail="No task found")


@app.get('/todos/{id}', response_model=Todo)
async def get_single_todo(id: int,session:Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id ==id)).first()
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail="No task found")


'''
put and patch both are used to edit: 
in put is used to delete the previous and add the new data, so we have to provide the complete data, 
in patch we have to put only those data whcih needs to be edited
'''
@app.put('/todos/{id}')
async def edit_todo(todo:Todo, session : Annotated[Session, Depends(get_session)]):
    exsisting_todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if exsisting_todo:
        exsisting_todo.content = Todo.content
        exsisting_todo.is_complete = Todo.is_complete
        session.add(exsisting_todo)
        session.commit()
        session.refresh(exsisting_todo)
        return exsisting_todo
    else:
        raise HTTPException(status_code=404, detail="No data Found", headers="Error")

@app.delete('/todos/{id}')
async def delete_todo(id: int, session: Annotated[Session, Depends(get_session)]):
    # deleted_todo = session.exec(select(Todo).where(id == id)).first()
    deleted_todo = session.get(Todo, id)
    if deleted_todo:
        session.delete(deleted_todo)
        session.commit()
        return{"message":"Todo Successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="No Todo found to e deleted")