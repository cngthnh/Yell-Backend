from flask import request
from ..loader import *
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from .auth_controller import tokenRequired
from ..views.message_view import getMessage
from ..views.transaction_view import genTransactionInfo

@tokenRequired
def createTransaction(uid):
    try:
        data = request.get_json()
        amount = int(data[API_AMOUNT])
        budgetId = str(data[API_BUDGET_ID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400
    
    currentBudget = db.session.query(Budget).filter_by(id=budgetId, owner_id=uid).first()
    if (currentBudget is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    transaction = Transaction(budgetId, amount)

    fields = data.keys()
    try:
        if (API_PURPOSES in fields and data[API_PURPOSES] is not None):
            transaction.purposes = str(data[API_PURPOSES])
        if (API_TIME in fields and data[API_TIME] is not None):
            transaction.time = datetime.fromisoformat(str(data[API_TIME]))
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400

    try:
        currentBudget.balance += amount
        currentBudget.transactions.append(transaction)
        db.session.add(currentBudget)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE, transaction_id=transaction.id), 200

@tokenRequired
def getTransaction(uid):
    try:
        transactionId = str(request.args[API_TRANSACTION_ID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400
    
    transaction = db.session.query(Transaction).filter_by(id=transactionId).first()
    if (transaction is None):
        return getMessage(TRANSACTION_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(Budget).join(UserAccount.budgets).\
        filter(Budget.id==transaction.budget_id, UserAccount.id==uid).first()
    if permissionCheck is None:
        return getMessage(FORBIDDEN_MESSAGE), 403

    return genTransactionInfo(transaction.dict()), 200

@tokenRequired
def updateTransaction(uid):
    try:
        data = request.get_json()
        transactionId = str(data[API_TRANSACTION_ID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400
    
    transaction = db.session.query(Transaction).filter_by(id=transactionId).first()
    if (transaction is None):
        return getMessage(TRANSACTION_DOES_NOT_EXISTS_MESSAGE), 404

    currentBudget = db.session.query(Budget).join(UserAccount.budgets).\
        filter(Budget.id==transaction.budget_id, UserAccount.id==uid).first()
    if currentBudget is None:
        return getMessage(FORBIDDEN_MESSAGE), 403

    try:
        fields = data.keys()
        if API_PURPOSES in fields and data[API_PURPOSES] is not None:
            transaction.purposes = str(data[API_PURPOSES])
        if API_TIME in fields and data[API_TIME] is not None:
            transaction.time = datetime.fromisoformat(data[API_TIME])
        if API_AMOUNT in fields and data[API_AMOUNT] is not None:
            currentBudget.balance += int(data[API_AMOUNT]) - transaction.amount
            transaction.amount = int(data[API_AMOUNT])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400
    
    transaction.updated_at = datetime.utcnow()

    try:
        db.session.add(transaction)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE), 200

@tokenRequired
def deleteTransaction(uid):
    try:
        data = request.get_json()
        transactionId = str(data[API_TRANSACTION_ID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400
    
    transaction = db.session.query(Transaction).filter_by(id=transactionId).first()
    if (transaction is None):
        return getMessage(TRANSACTION_DOES_NOT_EXISTS_MESSAGE), 404

    currentBudget = db.session.query(Budget).join(UserAccount.budgets).\
        filter(Budget.id==transaction.budget_id, UserAccount.id==uid).first()
    if currentBudget is None:
        return getMessage(FORBIDDEN_MESSAGE), 403
    
    try:
        currentBudget.balance -= transaction.amount
        db.session.delete(transaction)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE), 200