#!/usr/bin/env python3

import datetime

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

# def editSpell(spellId):
#     #TODO
#     return

def editSpell(spellId):
    # Pobieramy dane zaklęcia
    spell_data = session.getSpellData(spellId)
    if not spell_data:
        print("Nie znaleziono zaklęcia.")
        return

    spell_name, description, required_rank_name, required_rank_id, mana_consumption, owner_name, is_approved, is_rented, is_owner = spell_data

    print(f"Edytujesz zaklęcie: {spell_name}")
    print(f"Opis: {description}")
    print(f"Wymagana ranga: {required_rank_name}")
    print(f"Zużycie many: {mana_consumption}")

    new_name = questionary.text("Nowa nazwa zaklęcia (pozostaw puste, aby nie zmieniać):", default=spell_name).ask()
    new_description = questionary.text("Nowy opis zaklęcia (pozostaw puste, aby nie zmieniać):", default=description).ask()
    new_mana = questionary.text("Nowe zużycie many (pozostaw puste, aby nie zmieniać):", default=str(mana_consumption)).ask()

    ranks = session.listRanks()
    new_rank_name = questionary.select(
        "Nowa wymagana ranga (pozostaw pustą, aby nie zmieniać):",
        choices=[Choice(rank_name, rank_id) for rank_name, rank_id in ranks.items()] + [Choice("Brak zmiany", None)]
    ).ask()

    new_rank_id = new_rank_name if new_rank_name != "Brak zmiany" else required_rank_id
    new_mana = int(new_mana) if new_mana else mana_consumption

    session.updateSpell(spellId, new_name, new_description, new_rank_id, new_mana, None)  # rentalTerms pominięte

    print("Zaklęcie zostało zaktualizowane.")


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

# def displayRentals():
#
#     # TODO
#     return
def displayRentals():
    rented_spells = session.getRentedSpells()

    if rented_spells:
        print("Wypożyczone zaklęcia:")
        for spell_name, start_timestamp, end_timestamp in rented_spells:

            start_date = datetime.datetime.fromtimestamp(start_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            end_date = datetime.datetime.fromtimestamp(end_timestamp).strftime("%Y-%m-%d %H:%M:%S")

            print(f"Zaklęcie: {spell_name}")
            print(f"Data wypożyczenia: {start_date}")
            print(f"Data zwrotu: {end_date}")
            print("-" * 30)
    else:
        print("Nie wypożyczyłeś żadnych zaklęć.")

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
try:
    printSummary()

    main_menu = make_main_menu()
    while(True):
        main_menu.ask()()
except Exception as e:
    print(e)
    a= input()
