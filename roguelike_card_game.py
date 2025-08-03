import streamlit as st
import random
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from enum import Enum

# Configure Streamlit page
st.set_page_config(
    page_title="Dungeon Cards",
    page_icon="🗡️",
    layout="wide"
)

class CardType(Enum):
    ATTACK = "Attack"
    DEFENSE = "Defense"
    HEAL = "Heal"
    UTILITY = "Utility"

class EventType(Enum):
    COMBAT = "Combat"
    TREASURE = "Treasure"
    REST = "Rest"
    SHOP = "Shop"

@dataclass
class Card:
    name: str
    type: CardType
    cost: int
    damage: int = 0
    block: int = 0
    heal: int = 0
    description: str = ""

@dataclass
class Monster:
    name: str
    hp: int
    max_hp: int
    attack: int
    description: str
    gold_reward: int = 0
    card_reward: Optional[Card] = None

@dataclass
class Player:
    hp: int
    max_hp: int
    energy: int
    max_energy: int
    gold: int
    deck: List[Card]
    hand: List[Card]
    block: int = 0

# Game state initialization
def init_game_state():
    if 'player' not in st.session_state:
        starter_deck = [
            Card("Strike", CardType.ATTACK, 1, damage=6, description="Deal 6 damage"),
            Card("Strike", CardType.ATTACK, 1, damage=6, description="Deal 6 damage"),
            Card("Strike", CardType.ATTACK, 1, damage=6, description="Deal 6 damage"),
            Card("Strike", CardType.ATTACK, 1, damage=6, description="Deal 6 damage"),
            Card("Defend", CardType.DEFENSE, 1, block=5, description="Gain 5 block"),
            Card("Defend", CardType.DEFENSE, 1, block=5, description="Gain 5 block"),
            Card("Defend", CardType.DEFENSE, 1, block=5, description="Gain 5 block"),
            Card("Heal", CardType.HEAL, 2, heal=8, description="Restore 8 HP"),
        ]
        
        st.session_state.player = Player(
            hp=50, max_hp=50, energy=3, max_energy=3, gold=50,
            deck=starter_deck, hand=[], block=0
        )
        
    if 'floor' not in st.session_state:
        st.session_state.floor = 1
        
    if 'current_monster' not in st.session_state:
        st.session_state.current_monster = None
        
    if 'game_state' not in st.session_state:
        st.session_state.game_state = "map"  # map, combat, treasure, rest, shop, game_over
        
    if 'combat_log' not in st.session_state:
        st.session_state.combat_log = []

# Card definitions
def get_all_cards():
    return [
        Card("Fireball", CardType.ATTACK, 2, damage=12, description="Deal 12 damage"),
        Card("Lightning Bolt", CardType.ATTACK, 1, damage=8, description="Deal 8 damage"),
        Card("Shield Wall", CardType.DEFENSE, 2, block=12, description="Gain 12 block"),
        Card("Iron Skin", CardType.DEFENSE, 1, block=8, description="Gain 8 block"),
        Card("Potion", CardType.HEAL, 1, heal=5, description="Restore 5 HP"),
        Card("Greater Heal", CardType.HEAL, 3, heal=15, description="Restore 15 HP"),
        Card("Power Strike", CardType.ATTACK, 3, damage=18, description="Deal 18 damage"),
        Card("Quick Strike", CardType.ATTACK, 0, damage=3, description="Deal 3 damage"),
        Card("Barrier", CardType.DEFENSE, 3, block=20, description="Gain 20 block"),
        Card("Regeneration", CardType.HEAL, 2, heal=10, description="Restore 10 HP"),
    ]

# Monster definitions
def get_monsters_for_floor(floor):
    base_monsters = [
        Monster("Goblin", 20, 20, 5, "A small but vicious creature", 15),
        Monster("Orc", 35, 35, 8, "A brutish warrior", 25),
        Monster("Skeleton", 25, 25, 6, "Animated bones", 20),
        Monster("Spider", 15, 15, 4, "Eight-legged horror", 12),
        Monster("Bandit", 30, 30, 7, "A desperate criminal", 22),
    ]
    
    # Scale monsters with floor
    for monster in base_monsters:
        monster.hp += floor * 5
        monster.max_hp = monster.hp
        monster.attack += floor * 2
        monster.gold_reward += floor * 5
        
        # Chance for card reward
        if random.random() < 0.3:
            monster.card_reward = random.choice(get_all_cards())
    
    return base_monsters

# Combat functions
def draw_hand():
    player = st.session_state.player
    player.hand = []
    available_cards = player.deck.copy()
    hand_size = min(5, len(available_cards))
    
    for _ in range(hand_size):
        if available_cards:
            card = random.choice(available_cards)
            player.hand.append(card)
            available_cards.remove(card)

def play_card(card_index):
    player = st.session_state.player
    monster = st.session_state.current_monster
    
    if card_index >= len(player.hand):
        return
        
    card = player.hand[card_index]
    
    if player.energy < card.cost:
        st.session_state.combat_log.append("❌ Not enough energy!")
        return
    
    player.energy -= card.cost
    
    # Apply card effects
    if card.damage > 0:
        actual_damage = max(0, card.damage)
        monster.hp -= actual_damage
        st.session_state.combat_log.append(f"⚔️ {card.name} deals {actual_damage} damage!")
        
    if card.block > 0:
        player.block += card.block
        st.session_state.combat_log.append(f"🛡️ Gained {card.block} block!")
        
    if card.heal > 0:
        heal_amount = min(card.heal, player.max_hp - player.hp)
        player.hp += heal_amount
        st.session_state.combat_log.append(f"❤️ Healed {heal_amount} HP!")
    
    # Remove card from hand
    player.hand.pop(card_index)
    
    # Check if monster is defeated
    if monster.hp <= 0:
        st.session_state.combat_log.append(f"🏆 {monster.name} defeated!")
        player.gold += monster.gold_reward
        
        if monster.card_reward:
            player.deck.append(monster.card_reward)
            st.session_state.combat_log.append(f"📜 Gained {monster.card_reward.name}!")
        
        st.session_state.game_state = "map"
        st.session_state.current_monster = None
        st.session_state.floor += 1

def monster_turn():
    player = st.session_state.player
    monster = st.session_state.current_monster
    
    if monster and monster.hp > 0:
        damage = max(0, monster.attack - player.block)
        player.hp -= damage
        player.block = max(0, player.block - monster.attack)
        
        st.session_state.combat_log.append(f"💀 {monster.name} attacks for {damage} damage!")
        
        if player.hp <= 0:
            st.session_state.game_state = "game_over"

def end_turn():
    player = st.session_state.player
    
    # Monster attacks
    monster_turn()
    
    # Reset energy and block
    player.energy = player.max_energy
    player.block = 0
    
    # Draw new hand
    draw_hand()

# Event generation
def generate_event():
    events = [EventType.COMBAT, EventType.TREASURE, EventType.REST]
    if st.session_state.floor % 5 == 0:
        events.append(EventType.SHOP)
    
    return random.choice(events)

# UI Functions
def display_card(card, index=None, clickable=False):
    cost_color = "🟢" if st.session_state.player.energy >= card.cost else "🔴"
    
    card_text = f"""
    **{card.name}** {cost_color} {card.cost}
    
    {card.description}
    """
    
    if card.damage > 0:
        card_text += f"\n⚔️ Damage: {card.damage}"
    if card.block > 0:
        card_text += f"\n🛡️ Block: {card.block}"
    if card.heal > 0:
        card_text += f"\n❤️ Heal: {card.heal}"
    
    if clickable and index is not None:
        if st.button(card_text, key=f"card_{index}", use_container_width=True):
            play_card(index)
    else:
        st.markdown(card_text)

def display_player_stats():
    player = st.session_state.player
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("❤️ Health", f"{player.hp}/{player.max_hp}")
    with col2:
        st.metric("⚡ Energy", f"{player.energy}/{player.max_energy}")
    with col3:
        st.metric("🛡️ Block", player.block)
    with col4:
        st.metric("💰 Gold", player.gold)

def display_monster(monster):
    if monster:
        st.subheader(f"💀 {monster.name}")
        st.progress(monster.hp / monster.max_hp)
        st.write(f"HP: {monster.hp}/{monster.max_hp}")
        st.write(f"Attack: {monster.attack}")
        st.write(f"*{monster.description}*")

# Main game loop
def main():
    init_game_state()
    
    st.title("🗡️ Dungeon Cards")
    st.write(f"Floor: {st.session_state.floor}")
    
    display_player_stats()
    
    if st.session_state.game_state == "map":
        st.header("🗺️ Choose Your Path")
        
        event = generate_event()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⚔️ Combat", use_container_width=True):
                monsters = get_monsters_for_floor(st.session_state.floor)
                st.session_state.current_monster = random.choice(monsters)
                st.session_state.game_state = "combat"
                st.session_state.combat_log = []
                draw_hand()
                st.rerun()
        
        with col2:
            if st.button("💎 Treasure", use_container_width=True):
                st.session_state.game_state = "treasure"
                st.rerun()
        
        with col3:
            if st.button("🏕️ Rest", use_container_width=True):
                st.session_state.game_state = "rest"
                st.rerun()
    
    elif st.session_state.game_state == "combat":
        st.header("⚔️ Combat")
        
        monster = st.session_state.current_monster
        display_monster(monster)
        
        if st.session_state.combat_log:
            st.subheader("Combat Log")
            for log in st.session_state.combat_log[-5:]:  # Show last 5 logs
                st.write(log)
        
        st.subheader("Your Hand")
        if st.session_state.player.hand:
            cols = st.columns(len(st.session_state.player.hand))
            for i, card in enumerate(st.session_state.player.hand):
                with cols[i]:
                    display_card(card, i, clickable=True)
        else:
            st.write("No cards in hand")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 End Turn", use_container_width=True):
                end_turn()
                st.rerun()
        
        with col2:
            if st.button("🏃 Flee", use_container_width=True):
                st.session_state.game_state = "map"
                st.session_state.current_monster = None
                st.rerun()
    
    elif st.session_state.game_state == "treasure":
        st.header("💎 Treasure Room")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💰 Take Gold (25-50)", use_container_width=True):
                gold_found = random.randint(25, 50)
                st.session_state.player.gold += gold_found
                st.success(f"Found {gold_found} gold!")
                st.session_state.game_state = "map"
                st.rerun()
        
        with col2:
            if st.button("📜 Take Random Card", use_container_width=True):
                new_card = random.choice(get_all_cards())
                st.session_state.player.deck.append(new_card)
                st.success(f"Gained {new_card.name}!")
                st.session_state.game_state = "map"
                st.rerun()
    
    elif st.session_state.game_state == "rest":
        st.header("🏕️ Rest Site")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("😴 Rest (Heal 20 HP)", use_container_width=True):
                heal_amount = min(20, st.session_state.player.max_hp - st.session_state.player.hp)
                st.session_state.player.hp += heal_amount
                st.success(f"Healed {heal_amount} HP!")
                st.session_state.game_state = "map"
                st.rerun()
        
        with col2:
            if st.button("🔧 Upgrade (Remove a card)", use_container_width=True):
                if len(st.session_state.player.deck) > 5:  # Keep minimum deck size
                    card_to_remove = random.choice(st.session_state.player.deck)
                    st.session_state.player.deck.remove(card_to_remove)
                    st.success(f"Removed {card_to_remove.name} from deck!")
                else:
                    st.warning("Deck too small to remove cards!")
                st.session_state.game_state = "map"
                st.rerun()
    
    elif st.session_state.game_state == "game_over":
        st.header("💀 Game Over")
        st.write(f"You reached floor {st.session_state.floor}!")
        
        if st.button("🔄 Play Again", use_container_width=True):
            # Reset game state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Sidebar - Deck viewer
    with st.sidebar:
        st.header("📚 Your Deck")
        deck_counts = {}
        for card in st.session_state.player.deck:
            deck_counts[card.name] = deck_counts.get(card.name, 0) + 1
        
        for card_name, count in deck_counts.items():
            st.write(f"{card_name} x{count}")
        
        st.write(f"Total cards: {len(st.session_state.player.deck)}")

if __name__ == "__main__":
    main()