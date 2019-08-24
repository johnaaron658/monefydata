from datetime import datetime, timedelta	
from dateutil.relativedelta import relativedelta
from budgetAnalysisModel import BudgetAnalysisModel
from summaryModel import SummaryModel
from config import *
import analyzerInput as ai
import pandas as pd
import glob
import os

def main():
	# optional inputs
    # today = datetime.strptime('2019/07/20','%Y/%m/%d')
    today = datetime.now()
	
    # initialize inputs
    incomeList = getIncomeList()
    budgetList = getBudgetList()
    payday = getPayday()
    tranDf = getTransactionDataFrame()
    recentPayday = getRecentPayday(date=today, payday=payday)
    nextPayday = getNextPayday(date=today, payday=payday)

    # filter dataframe
    tranDf = tranDf[tranDf[COLUMN_DATE] >= recentPayday]
    tranDf = tranDf[tranDf[COLUMN_DATE] <= nextPayday]
    # print(tranDf[tranDf[COLUMN_CATEGORY].isin(incomeList)][COLUMN_AMOUNT])

    # prepare constant values
    income = getIncome(incomeList, tranDf)

    # initialize summary model
    summaryModel = SummaryModel()

    for budget in budgetList:
        # initialize budget analysis model
        budgetAnalysisModel = BudgetAnalysisModel()

        # computations
        allocatedBudget = budget.allocation * income - budget.fixedExpense + budget.carryOver
        expectedExpense = getExpectedExpenseToDate(allocatedBudget, recentPayday, nextPayday, today)
        actualExpense = getActualExpense(budget.categoryList, tranDf)
        net = expectedExpense - actualExpense
        remainingBalance = allocatedBudget - actualExpense

        # save budget analysis model
        budgetAnalysisModel.name = budget.name
        budgetAnalysisModel.allocation = allocatedBudget
        budgetAnalysisModel.expected_expense = expectedExpense
        budgetAnalysisModel.actual_expense = actualExpense
        budgetAnalysisModel.net = net
        budgetAnalysisModel.remain = remainingBalance
        budgetAnalysisModel.frequency = budget.frequency
        if budget.frequency == DAILY and (nextPayday - today).days != 0:
            budgetAnalysisModel.suggestion = remainingBalance/(nextPayday - today).days
        elif budget.frequency == WEEKLY and ((nextPayday - today).days/7) != 0:
            budgetAnalysisModel.suggestion = remainingBalance/((nextPayday - today).days//7)
        elif budget.frequency == MONTHLY:
            budgetAnalysisModel.suggestion = remainingBalance

        # update summary model
        summaryModel.budget_analysis_list.append(budgetAnalysisModel)
        summaryModel.overall_net += budgetAnalysisModel.net
        summaryModel.overall_remain += budgetAnalysisModel.remain

    outputAnalysisReport(summaryModel, today)
        

def getBudgetList():
    return ai.budgetList

def getIncomeList():
    return ai.incomeList

def getPayday():
    return ai.payday

def getTransactionDataFrame():
    mostRecentCsv = max(glob.iglob(COMMON_DATA_SRC_PATH 
    															+ COMMON_ALL_FILE_SELECT 
    															+ COMMON_DATA_SRC_CSV), 
    															key=os.path.getmtime)
    df = pd.read_csv(mostRecentCsv, thousands=',')
    df[COLUMN_AMOUNT] = df[COLUMN_AMOUNT].abs()
    df[COLUMN_DATE] = pd.to_datetime(format=COMMON_DATE_FORMAT,arg=df[COLUMN_DATE])
    return df

def getRecentPayday(date=datetime.now(), payday=24):
    thisPayday = date - relativedelta(months=0, day=payday)
    lastPayday = date - relativedelta(months=1, day=payday)
    if (date - thisPayday).days >= 0:
        return thisPayday.replace(hour=0,minute=0,second=0,microsecond=0)
    return lastPayday.replace(hour=0,minute=0,second=0,microsecond=0)

def getNextPayday(date=datetime.now(), payday=24):
    thisPayday = date + relativedelta(months=0, day=payday)
    nextPayday = date + relativedelta(months=1, day=payday)
    returnDate = thisPayday.replace(hour=0,minute=0,second=0,microsecond=0)
    if (date - thisPayday).days >= 0:
        returnDate = nextPayday.replace(hour=0,minute=0,second=0,microsecond=0)
    returnDate = returnDate - timedelta(days=1)
    return returnDate.replace(hour=23, minute=59, second=59, microsecond=59)

def getIncome(incomeList, df):
    incomes = df[df[COLUMN_CATEGORY].isin(incomeList)]
    return incomes[COLUMN_AMOUNT].sum()

def getExpectedExpenseToDate(allocationAmount, recentPayday, nextPayday, today=datetime.now()):
    budgetPerDay = allocationAmount/(nextPayday - recentPayday).days
    return budgetPerDay * ((today - recentPayday).days + 1)

def getActualExpense(categoryList, df):
    expenses = df[df[COLUMN_CATEGORY].isin(categoryList)]
    return expenses[COLUMN_AMOUNT].sum()

def outputAnalysisReport(summaryModel, today=datetime.now()):
    with open(COMMON_ANALYSIS_REPORT_FILEPATH 
    + COMMON_ANALYSIS_REPORT_FILENAME + '_' 
    + today.strftime(COMMON_DATE_PRINT_FORMAT) 
    + COMMON_ANALYSIS_REPORT_FILE_TYPE, 'w') as f:
        print(BUDGET_LIST, file=f)
        for budgetAnalysisModel in summaryModel.budget_analysis_list:
            print(BUDGET_SEPARATOR, file=f)
            printWithColon(BUDGET_NAME, budgetAnalysisModel.name, f)
            printWithColon(BUDGET_ALLOCATION, budgetAnalysisModel.allocation, f)
            printWithColon(BUDGET_EXPECTED_EXPENSE, budgetAnalysisModel.expected_expense, f)
            printWithColon(BUDGET_ACTUAL_EXPENSE, budgetAnalysisModel.actual_expense, f)
            printWithColon(BUDGET_NET, budgetAnalysisModel.net, f)
            printWithColon(BUDGET_REMAIN, budgetAnalysisModel.remain, f)
            if budgetAnalysisModel.frequency == DAILY:
                printWithColon(BUDGET_FREQUENCY, DAILY_STR, f)
            elif budgetAnalysisModel.frequency == WEEKLY:
                printWithColon(BUDGET_FREQUENCY, WEEKLY_STR, f)
            elif budgetAnalysisModel.frequency == MONTHLY:
                printWithColon(BUDGET_FREQUENCY, MONTHLY_STR, f)
            printWithColon(BUDGET_SUGGESTION, budgetAnalysisModel.suggestion, f)
            print(BUDGET_SEPARATOR, file=f)
        printWithColon(OVERALL_NET, summaryModel.overall_net, f)
        printWithColon(OVERALL_REMAIN, summaryModel.overall_remain, f)

def printWithColon(key, val, f):
    print(key + ':' + str(val), file=f)

main()