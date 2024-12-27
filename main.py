#!/usr/bin/env python3

import questionary
from questionary import Choice

from getpass import getpass
from backend import *

def addSpell():
    session.addSpell(
        questionary.text("Nazwa zaklęcia").ask(),
        questionary.text("Opis").ask(),
        questionary.select(
            "Wymagana ranga",
            choices = [Choice(f"{rankName}", id) for rankName, id in session.listRanks().items()]
        ).ask(),
        questionary.text("Konsumpcja many").ask(),
    )
    
def printSummary():
    username, rankname, isCurator, curRentals, maxRentals = session.getUserSummary()

    if(isCurator): title = f"Kustosz {rankname}"
    else: title = rankname

    print(f"Zalogowano jako {username} ({title}).")
    print(f"Twój stan wypożyczeń: {curRentals} / {maxRentals}")

def setRank():
    wizardId = questionary.select(
        "Wybierz czarodzieja",
        choices = [Choice(f"{nick} - {rankName}", id) for id, nick, rankName in session.listWizards()] + [Choice("Wyjdź", -1)]
    ).ask()

    if wizardId == -1: return
    
    rankId = questionary.select(
        "Ustaw rangę",
        choices = [Choice(f"{rankName}", id) for rankName, id in session.listRanks().items()] + [Choice("Wyjdź", -1)]
    ).ask()

    if rankId == -1: return

    session.setRank(wizardId, rankId)

def listRentals():
    pass

def nop(*args): return

def shorten(text, limit=80):
    text = text.replace("\n", " ").replace("\t", " ")
    if(len(text) >= limit):
        return text[:limit-3] + "..."
    else:
        return text

def editSpell(spellId):
    #TODO
    return

def rentSpell(spellId):
    session.rentSpell(spellId, questionary.text("Czas wypożyczenia (dni)").ask())

def browseSpells(spells):
    spellId = questionary.select(
        "Wybierz zaklęcie",
        choices = [Choice(f"{name} - {shorten(description)}", id) for id, name, description in spells] + [Choice("Wyjdź", -1)]
    ).ask()

    if(spellId == -1): return

    spellName, description, requiredRankName, requiredRankId, manaConsumption, ownerName, isApproved, isRented, isOwner = session.getSpellData(spellId)
    print(f"nazwa: {spellName}")
    print(f"opis: {description}")
    print(f"zużycie many: {manaConsumption}")
    print(f"wymagana ranga: {requiredRankName}")
    print(f"właściciel: {ownerName}")

    userRank = session.getRank()
    isCurator = session.isCurator()

    choices = [Choice("Wyjdź", nop)]

    if(isApproved and requiredRankId <= userRank):
        if(isRented):
            choices.append(Choice("Oddaj", session.unrentSpell))
        else:
            choices.append(Choice("Wypożycz", rentSpell))

    if(isCurator and not isApproved):
        choices.append(Choice("Zatwierdź publikację", session.approveSpell))

    if(isCurator or isOwner):
        choices += [
            Choice("Edytuj", editSpell),
            Choice("Usuń", session.removeSpell),
        ]

    questionary.select(
        "Co chcesz zrobić z zaklęciem",
        choices = choices
    ).ask()(spellId)

def browseAvailableSpells():
    browseSpells(session.listAvailableSpells())
    
def searchAvailableSpells():
    # TODO
    browseSpells(session.searchAvailableSpells(
           questionary.text("Wyszukaj zaklęcie na podstawie nazwy i opisu").ask()
     ))

def browseSpellsToApprove():
    browseSpells(session.listSpellsToApprove())
    
def browseAllSpells():
    browseSpells(session.listAllSpells())

def displayRentals():
    # TODO
    return

def make_main_menu():
    choices=[
        Choice("Dodawanie zaklęcia", addSpell),
        Choice("Przeglądaj dostępne zaklęcia", browseAvailableSpells),
        Choice("Wyszukaj dostępne zaklęcie", searchAvailableSpells),
        Choice("Wyświetl wypożyczenia", displayRentals),
        Choice("Wyjdź", lambda : exit(0)),
    ]
    if(session.isCurator()):
        choices = [
            Choice("Nadaj rangę", setRank),
            Choice("Przeglądaj niezakceptowane zaklęcia", browseSpellsToApprove),
            Choice("Przeglądaj wszystkie zaklęcia", browseAllSpells),
            questionary.Separator(""),
        ] + choices
    return questionary.select("Co chcesz zrobić?", choices=choices)
    
session = questionary.select(
    "Co chcesz zrobić?",
    choices = [
        Choice("Rejestracja", register),
        Choice("Logowanie", login)
    ]
).ask()(
    questionary.text("Nazwa użytkownika").ask(),
    questionary.password("Hasło").ask()
)

printSummary()

main_menu = make_main_menu()
while(True):
    main_menu.ask()()
