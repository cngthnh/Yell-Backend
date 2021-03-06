from flask import request
from ..loader import *
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from ..views.budget_view import genBudgetInfo
from .auth_controller import tokenRequired
from ..views.message_view import getMessage

@tokenRequired
def createBudget(uid):
    try:
        data = request.get_json()
        name = str(data[API_NAME])
        balance = int(data[API_BALANCE])
        btype = int(data[API_TYPE])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    budget = Budget(uid, 
                name, 
                balance,
                btype)
    
    fields = data.keys()

    try:
        if (API_THRESHOLD in fields and data[API_THRESHOLD] is not None):
            budget.threshold = int(data[API_THRESHOLD])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    try:
        db.session.add(budget)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE, budget_id=str(budget.id)), 200

@tokenRequired
def getBudget(uid):
    try:
        _budgetId = str(request.args[API_BUDGET_ID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    budget = db.session.query(Budget).filter_by(owner_id=uid, id=_budgetId).first()

    if budget is None:
        return getMessage(message=BUDGET_DOES_NOT_EXISTS_MESSAGE), 404

    fetchType = request.args.get(API_FETCH)
    if (fetchType==API_FULL):
        return genBudgetInfo(budget.dict()), 200
    elif (fetchType==API_COMPACT):
        return genBudgetInfo(budget.compactDict()), 200
    else:
        return genBudgetInfo(budget.compactDict()), 200

@tokenRequired
def updateBudget(uid):
    try:
        data = request.get_json()
        _budgetId = str(data[API_BUDGET_ID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    budget = db.session.query(Budget).filter_by(id=_budgetId, owner_id=uid).first()
    if budget is None:
        return getMessage(message=BUDGET_DOES_NOT_EXISTS_MESSAGE), 404

    fields = data.keys()

    try:
        if API_NAME in fields and data[API_NAME] is not None:
            budget.name = str(data[API_NAME])
        if API_BALANCE in fields and data[API_BALANCE] is not None:
            budget.balance = int(data[API_BALANCE])
        if API_TYPE in fields and data[API_TYPE] is not None:
            budget.btype = int(data[API_TYPE])
        if API_THRESHOLD in fields and data[API_THRESHOLD] is not None:
            budget.threshold = int(data[API_THRESHOLD])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    budget.updated_at = datetime.utcnow()

    try:
        db.session.add(budget)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE), 200

@tokenRequired
def deleteBudget(uid):
    try:
        data = request.get_json()
        _budgetId = str(data[API_BUDGET_ID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    budget = db.session.query(Budget).filter_by(id=_budgetId, owner_id=uid).first()

    if (budget is None):
        return getMessage(message=BUDGET_DOES_NOT_EXISTS_MESSAGE), 404

    try:
        db.session.delete(budget)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE), 200
