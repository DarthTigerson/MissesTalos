from fastapi import APIRouter, Depends, status, HTTPException, Request, Form, Response
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from database import SessionLocal, engine
from pydantic import BaseModel, Field
from models import Users, Roles, Teams, Base
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext

from starlette import status
from starlette.responses import RedirectResponse

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

templates = Jinja2Templates(directory='templates')

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(Users)\
        .filter(Users.username == username)\
        .first()

    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(username: str, role_id: int,
                        expires_delta: Optional[timedelta] = None):

    encode = {"sub": username, "role_id": role_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role_id: int = payload.get("role_id")
        if username is None or role_id is None:
            return None
        return {"username": username, "role_id": role_id}
    except JWTError:
        token = request.cookies.get("access_token")
        del token
        RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    token_expires = timedelta(minutes=300)
    token = create_access_token(user.username,
                                user.role_id,
                                expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True

@router.get("/")
async def test(request: Request, db: Session = Depends(get_db)):
    users = db.query(Users).order_by(Users.username).all()
    roles = db.query(Roles).order_by(Roles.name).all()
    teams = db.query(Teams).order_by(Teams.name).all()

    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "roles": roles, "teams": teams})

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response, form_data=form, db=db)
        if not validate_user_cookie:
            msg = "Incorrect username or password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@router.get("/add_role")
async def add_role(request: Request):
    return templates.TemplateResponse("add-role.html", {"request": request})

@router.post("/add_role", response_class=HTMLResponse)
async def create_role(request: Request, name: str = Form(...), description: str = Form(None), onboarding: bool = Form(False), employee_updates: bool = Form(False), offboarding: bool = Form(False), manage_modify: bool = Form(False), admin: bool = Form(False), payroll: bool = Form(False), api_report: bool = Form(False), db: Session = Depends(get_db)):
    role_model = Roles()

    role_model.name = name
    role_model.description = description
    role_model.onboarding = onboarding
    role_model.employee_updates = employee_updates
    role_model.offboarding = offboarding
    role_model.manage_modify = manage_modify
    role_model.admin = admin
    role_model.payroll = payroll
    role_model.api_report = api_report

    db.add(role_model)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/edit_role/{role_id}")
async def edit_role(request: Request, role_id: int, db: Session = Depends(get_db)):
    role = db.query(Roles).filter(Roles.id == role_id).first()
    
    return templates.TemplateResponse("edit-role.html", {"request": request, "role": role})

@router.post("/edit_role/{role_id}", response_class=HTMLResponse)
async def edit_role(request: Request, role_id: int, name: str = Form(...), description: str = Form(None), onboarding: bool = Form(False), employee_updates: bool = Form(False), offboarding: bool = Form(False), manage_modify: bool = Form(False), admin: bool = Form(False), payroll: bool = Form(False), api_report: bool = Form(False), db: Session = Depends(get_db)):
    role = db.query(Roles).filter(Roles.id == role_id).first()

    role.name = name
    role.description = description
    role.onboarding = onboarding
    role.employee_updates = employee_updates
    role.offboarding = offboarding
    role.manage_modify = manage_modify
    role.admin = admin
    role.payroll = payroll
    role.api_report = api_report

    db.add(role)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/add_team")
async def add_team(request: Request):
    return templates.TemplateResponse("add-team.html", {"request": request})

@router.post("/add_team", response_class=HTMLResponse)
async def create_team(request: Request, name: str = Form(...), description: str = Form(None), db: Session = Depends(get_db)):
    team_model = Teams()

    team_model.name = name
    team_model.description = description

    db.add(team_model)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/edit_team/{team_id}")
async def edit_team(request: Request, team_id: int, db: Session = Depends(get_db)):
    team = db.query(Teams).filter(Teams.id == team_id).first()
    
    return templates.TemplateResponse("edit-team.html", {"request": request, "team": team})

@router.post("/edit_team/{team_id}", response_class=HTMLResponse)
async def update_team(request: Request, team_id: int, name: str = Form(...), description: str = Form(None), db: Session = Depends(get_db)):
    team = db.query(Teams).filter(Teams.id == team_id).first()

    team.name = name
    team.description = description

    db.add(team)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/add_user")
async def add_user(request: Request, db: Session = Depends(get_db)):
    roles = db.query(Roles).order_by(Roles.name).all()
    teams = db.query(Teams).order_by(Teams.name).all()

    return templates.TemplateResponse("add-user.html", {"request": request, "roles": roles, "teams": teams})

@router.post("/add_user", response_class=HTMLResponse)
async def create_user(request: Request, username: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), role_id: int = Form(...), team_id: int = Form(None), password: str = Form(...), db: Session = Depends(get_db)):
    user_model = Users()

    user_model.username = username
    user_model.first_name = first_name
    user_model.last_name = last_name
    user_model.role_id = role_id
    user_model.team_id = team_id
    user_model.password = get_password_hash(password)

    db.add(user_model)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/edit_user/{user_id}")
async def edit_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user_id).first()
    roles = db.query(Roles).order_by(Roles.name).all()
    teams = db.query(Teams).order_by(Teams.name).all()
    
    return templates.TemplateResponse("edit-user.html", {"request": request, "user": user, "roles": roles, "teams": teams})

@router.post("/edit_user/{user_id}", response_class=HTMLResponse)
async def update_user(request: Request, user_id: int, username: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), role_id: int = Form(...), team_id: int = Form(...), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user_id).first()

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.role_id = role_id
    user.team_id = team_id

    db.add(user)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

#Exceptions
def get_user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def token_exception():
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return token_exception_response