# This example requires the 'message_content' intent.

import discord

import re
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

discordToken = os.getenv("DISCORD_TOKEN")

#commands
def currency(input):
    conversion = {'pp': 1000, 'gp': 100, 'ep': 50, 'sp': 10, 'cp': 1,}

    total_copper = 0
    pattern = r'([+-])?\s*(\d+)\s*(pp|gp|ep|sp|cp)\s*(?:(\*|/)\s*(\d+))?'
    matches = re.findall(pattern, input.lower())

    for sign, amount, denomination, op, operand in matches:
        value = int(amount) * conversion[denomination]

        if op == '*' and operand:
            value *= int(operand)
        elif op == '/' and operand:
            value //= int(operand)

        if sign == '-':
            value = -value

        total_copper += value

    
    ordered = [('pp', 1000), ('gp', 100), ('ep', 50), ('sp', 10), ('cp', 1)]

    # Build each representation, dropping the largest denomination each time
    results = []
    for start in range(len(ordered)):
        remaining = total_copper
        parts = []
        for denom, rate in ordered[start:]:
            if remaining >= rate:
                count = remaining // rate
                remaining %= rate
                parts.append(f"{count}{denom}")
        if parts:
            result = ' '.join(parts)
            if not results or result != results[-1]:
                results.append(result)

    return '\n'.join(results) if results else "0cp"
def rollDice(notation: str) -> int:
    """
    Rolls dice based on notation like '2d6+1d4-1d2'.
    Accepts optional 'adv' or 'dis' prefix on any xdy token.
      adv: rolls each xdy group twice, takes the higher result
      dis: rolls each xdy group twice, takes the lower result
    """
    notation = notation.replace(" ", "").lower()
    tokens = re.findall(r'[+-]?(?:(?:adv|dis)?\d+d\d+|\d+)', notation)

    total = 0
    for token in tokens:
        if token.startswith('-'):
            sign = -1
            token = token[1:]
        elif token.startswith('+'):
            sign = 1
            token = token[1:]
        else:
            sign = 1

        clean, mode = parseNotation(token)

        if 'd' in clean:
            num_dice, faces = clean.split('d')
            num_dice = int(num_dice) if num_dice else 1
            faces = int(faces)

            if mode in ('adv', 'dis'):
                roll_a = sum(random.randint(1, faces) for _ in range(num_dice))
                roll_b = sum(random.randint(1, faces) for _ in range(num_dice))
                roll_result = max(roll_a, roll_b) if mode == 'adv' else min(roll_a, roll_b)
                print(f"rolling {num_dice}d{faces} with {'advantage' if mode == 'adv' else 'disadvantage'}: {roll_a} vs {roll_b} → {roll_result}")
            else:
                roll_result = sum(random.randint(1, faces) for _ in range(num_dice))
                print(f"rolling {num_dice} dice with {faces} faces: {roll_result}")
        else:
            roll_result = int(clean)
            print(f"adding flat modifier {roll_result}")

        total += sign * roll_result

    return total
def diceCalcs(input):
    print(input)
    optionFlags = ["all", "basic", "normal graph", "cum graph", "graphs"]
    options = ""
    for flag in optionFlags:
        if flag in input:
            options += flag + ", "
            input = re.sub(flag, "", input)
    
    print(options)

    out = "Overview for the dice roll " + input + ":\n\n"
    files = []

    if "basic" in options or options == "" or "all" in options:
        arr = basicCalcs(input)
        out += "Lowest roll: " + str(arr['lowest']) + "\n"
        out += "Average roll: " + str(arr['average']) + "\n"
        out += "Highest roll: " + str(arr['highest']) + "\n"

    if "ndist" in options or "graphs" in options or "all" in options:
        rolls, probs = diceDistribution(input)
        generateGraph(input, rolls, probs, False, "nGraph.png")
        with open('nGraph.png', 'rb') as f:
            files.append(discord.File(f))

    if "cdist" in options or "graphs" in options or "all" in options:
        rolls, probs = diceDistribution(input)
        generateGraph(input, rolls, probs, True, "cGraph.png")
        with open('cGraph.png', 'rb') as f:
            files.append(discord.File(f))

    return out, files
def diceCalcChance(input: str) -> str:
    """
    Calculates the chance of notation_a rolling higher or lower than notation_b.

    Args:
        notation_a: First dice notation string  e.g. '2d6'
        notation_b: Second dice notation string e.g. '1d8+2'
        operator:   Comparison operator — one of:
                      '>'   notation_a strictly greater than notation_b
                      '>='  notation_a greater than or equal to notation_b
                      '<'   notation_a strictly less than notation_b
                      '<='  notation_a less than or equal to notation_b
                      '='   notation_a exactly equal to notation_b

    Returns:
        A formatted string describing the chance.
    """

    input = input.replace(" ", "").lower()

    match = re.match(r'^(.+?)(>=|<=|>|<|=)(.+)$', input)
    if not match:
        raise ValueError(
            f"Could not parse '{input}'. "
            "Expected format: 'notation_a operator notation_b' "
            "where operator is one of: > >= < <= ="
        )

    notation_a = match.group(1)
    operator   = match.group(2)
    notation_b = match.group(3)

    if operator not in ('>', '>=', '<', '<=', '='):
        raise ValueError(f"Invalid operator '{operator}'. Use one of: > >= < <= =")

    # Get the full probability distributions for both notations
    rolls_a, probs_a = diceDistribution(notation_a)
    rolls_b, probs_b = diceDistribution(notation_b)

    # Convert to dicts for easy lookup  {roll_value: probability_fraction}
    dist_a = {r: p / 100 for r, p in zip(rolls_a, probs_a)}
    dist_b = {r: p / 100 for r, p in zip(rolls_b, probs_b)}

    # Sum over all (a, b) pairs that satisfy the operator
    chance = 0.0
    for val_a, prob_a in dist_a.items():
        for val_b, prob_b in dist_b.items():
            if operator == '>'  and val_a >  val_b: chance += prob_a * prob_b
            if operator == '>=' and val_a >= val_b: chance += prob_a * prob_b
            if operator == '<'  and val_a <  val_b: chance += prob_a * prob_b
            if operator == '<=' and val_a <= val_b: chance += prob_a * prob_b
            if operator == '='  and val_a == val_b: chance += prob_a * prob_b

    chance_pct = chance * 100

    op_label = {
        '>':  'higher than',
        '>=': 'higher than or equal to',
        '<':  'lower than',
        '<=': 'lower than or equal to',
        '=':  'the same as',
    }[operator]

    out = (
        f"Chance of {notation_a.upper()} rolling {op_label} {notation_b.upper()}: "
        f"{chance_pct:.2f}%"
    )
    if 'd' in notation_a and 'd' in notation_b: 
        if '>' in operator:
            out += "\nthat means that "
            if (chance_pct > 50): 
                out += notation_a.upper() + " rolls higher"
            elif (chance_pct < 50):
                out += notation_b.upper() + " rolls higher"
            else:
                out += notation_a.upper() + " and " + notation_b.upper() + " are the same"
        elif '<' in operator:
            out += "\nthat means that "
            if (chance_pct > 50): 
                out += notation_a.upper() + " rolls lower"
            elif (chance_pct < 50):
                out += notation_b.upper() + " rolls lower"
            else:
                out += notation_a.upper() + " and " + notation_b.upper() + " are the same"
        
    return out

#helper functions
def parseNotation(notation: str) -> tuple[str, str]:
    """
    Strips an optional 'adv' or 'dis' prefix from a notation string.

    Args:
        notation: e.g. 'adv1d20+2', 'dis2d6', '1d8'

    Returns:
        (clean_notation, mode) where mode is 'adv', 'dis', or 'normal'
    """
    notation = notation.replace(" ", "").lower()

    if notation.startswith("adv"):
        return notation[3:], "adv"
    elif notation.startswith("dis"):
        return notation[3:], "dis"
    else:
        return notation, "normal"
def basicCalcs(input): 
    """
    Calculates the lowest, highest, and average possible rolls for a dice notation.
    Average is derived from the exact probability distribution, so adv/dis is reflected correctly.
    """
    rolls, probs = diceDistribution(input)

    lowest  = rolls[0]
    highest = rolls[-1]
    average = sum(r * (p / 100) for r, p in zip(rolls, probs))

    return {
        "lowest":  lowest,
        "average": average,
        "highest": highest
    }
def diceDistribution(notation: str) -> tuple:
    notation = notation.replace(" ", "").lower()
    tokens = re.findall(r'[+-]?(?:(?:adv|dis)?\d+d\d+|\d+)', notation)

    groups = []
    for token in tokens:
        if token.startswith('-'):
            sign, token = -1, token[1:]
        elif token.startswith('+'):
            sign, token = +1, token[1:]
        else:
            sign = +1

        clean, mode = parseNotation(token)

        if 'd' in clean:
            num_dice, faces = clean.split('d')
            num_dice = int(num_dice) if num_dice else 1
            faces    = int(faces)
            groups.append((sign, [faces] * num_dice, mode))
        else:
            groups.append((sign, [int(clean)], 'normal'))

    dist: dict[int, float] = {0: 1.0}

    for sign, faces_list, mode in groups:
        # For adv/dis, the whole group (e.g. 2d6) is rolled twice — take max/min
        if mode in ('adv', 'dis'):
            # Build the distribution for one roll of this group
            group_dist: dict[int, float] = {0: 1.0}
            for faces in faces_list:
                new_d: dict[int, float] = defaultdict(float)
                prob = 1.0 / faces
                for outcome in range(1, faces + 1):
                    for k, p in group_dist.items():
                        new_d[k + outcome] += p * prob
                group_dist = dict(new_d)

            # Combine two independent rolls, keeping max (adv) or min (dis)
            adv_dist: dict[int, float] = defaultdict(float)
            for r1, p1 in group_dist.items():
                for r2, p2 in group_dist.items():
                    result = max(r1, r2) if mode == 'adv' else min(r1, r2)
                    adv_dist[result] += p1 * p2

            # Convolve the adv/dis result into the main distribution with sign
            new_dist: dict[int, float] = defaultdict(float)
            for outcome, p_out in adv_dist.items():
                for k, p in dist.items():
                    new_dist[k + sign * outcome] += p * p_out
            dist = dict(new_dist)

        else:
            for faces in faces_list:
                if faces == 1:
                    dist = {k + sign * 1: p for k, p in dist.items()}
                else:
                    new_dist: dict[int, float] = defaultdict(float)
                    face_prob = 1.0 / faces
                    for outcome in range(1, faces + 1):
                        for k, p in dist.items():
                            new_dist[k + sign * outcome] += p * face_prob
                    dist = dict(new_dist)

    rolls = sorted(dist.keys())
    probs = [dist[r] * 100 for r in rolls]
    return rolls, probs
def generateGraph(notation: str, rolls, probs, cumulative: bool = False, filename: str = "Graph.png") -> None:
    """
    Generates a probability distribution graph for a dice notation string.

    Args:
        notation:   A string in xdy format with optional +/- operations
                    e.g. '2d6', '1d20+2d4', '3d8-1d6+2d4'
        cumulative: If True, plots a cumulative distribution (CDF).
                    If False (default), plots a normal probability distribution (PDF).
    """

     # ------------------------------------------------------------------ #
    #  3. Build cumulative probabilities if requested                     #
    # ------------------------------------------------------------------ #
    if cumulative:
        cum = []
        running = 0.0
        for p in probs:
            running += p
            cum.append(running)
        y_values = cum
        y_label  = "Cumulative Probability (%)"
        title_suffix = "Cumulative Distribution"
    else:
        y_values = probs
        y_label  = "Probability (%)"
        title_suffix = "Probability Distribution"
   
    # ------------------------------------------------------------------ #
    #  4. Plot                                                            #
    # ------------------------------------------------------------------ #
    BG        = "#0f0f13"
    PANEL     = "#1a1a24"
    ACCENT    = "#c084fc"       # purple
    ACCENT2   = "#38bdf8"       # sky blue  (gradient feel in bars)
    TEXT      = "#e2e8f0"
    SUBTEXT   = "#64748b"
    GRID      = "#2a2a3a"

    fig, ax = plt.subplots(figsize=(max(10, len(rolls) * 0.35 + 2), 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    # Colour gradient across bars
    n = len(rolls)
    colors = [
        tuple(
            (1 - t) * np.array([0.75, 0.51, 0.99])   # ACCENT  rgb
            + t      * np.array([0.22, 0.74, 0.97])   # ACCENT2 rgb
        )
        for t in np.linspace(0, 1, n)
    ]

    bars = ax.bar(rolls, y_values, color=colors, width=0.7,
                  zorder=3, linewidth=0)

    # Highlight the peak bar with a white edge
    # peak_idx = int(np.argmax(y_values))
    # bars[peak_idx].set_edgecolor("white")
    # bars[peak_idx].set_linewidth(1.2)

    # Value labels on bars (only if not too many)
    if n <= 40:
        for bar, val in zip(bars, y_values):
            if val >= 0.5:          # skip near-zero labels
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(y_values) * 0.012,
                    f"{val:.1f}%",
                    ha='center', va='bottom',
                    fontsize=7, color=TEXT, alpha=0.75,
                    fontfamily='monospace'
                )

    # Axes styling
    ax.set_xlabel("Roll Total", color=TEXT, fontsize=11, labelpad=8)
    ax.set_ylabel(y_label,      color=TEXT, fontsize=11, labelpad=8)
    ax.set_title(
        f"{notation.upper()}  —  {title_suffix}",
        color=TEXT, fontsize=14, fontweight='bold', pad=14
    )

    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=30))
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)

    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%'))
    ax.set_ylim(0, max(y_values) * 1.18)
    ax.grid(axis='y', color=GRID, linewidth=0.6, zorder=0)
    ax.set_xlim(rolls[0] - 0.8, rolls[-1] + 0.8)

    # Stats annotation box
    stats = basicCalcs(notation)
    mean_val = stats["average"]
    ax.axvline(mean_val, color=ACCENT, linewidth=1.2,
               linestyle='--', alpha=0.8, zorder=4)
    ax.text(
        mean_val, max(y_values) * 1.10,
        f"avg {mean_val:.1f}",
        color=ACCENT, fontsize=8, ha='center',
        fontfamily='monospace'
    )

    info = (f"min {stats['lowest']}   "
            f"max {stats['highest']}   "
            f"avg {stats['average']:.2f}")
    fig.text(0.5, 0.01, info, ha='center', color=SUBTEXT,
             fontsize=9, fontfamily='monospace')

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(filename,
                dpi=150, bbox_inches='tight', facecolor=BG)


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!money '):
        out = currency(message.content[7:])
        await message.channel.send(out)

    if message.content.startswith('!roll '):
        input = message.content[6:]
        out = "Rolling " + input + ": "
        if "adv" in input:
            input = re.sub("adv", "", input)
            out += " (with advantage)\n"
            roll1 = rollDice(input)
            roll2 = rollDice(input)
            out += "You rolled " + str(roll1) + " and " + str(roll2) + " = " + str(max(roll2,roll1))
        elif "dis" in input:
            input = re.sub("adv", "", input)
            out += " (with disadvantage)\n"
            roll1 = rollDice(input)
            roll2 = rollDice(input)
            out += "You rolled " + str(roll1) + " and " + str(roll2) + " = " + str(min(roll2,roll1))
        else:
            out += "You rolled " + str(rollDice(input))
        await message.channel.send(out)

    if message.content.startswith('!analyse '):
        out, files = diceCalcs(message.content[9:])
        await message.channel.send(out)
        for f in files:
            await message.channel.send(file=f)

    if message.content.startswith('!chance '):
        out = diceCalcChance(message.content[8:])
        await message.channel.send(out)

    if message.content == '!help dnd':
        out = """Commands:
        !money:
        Give a notation of an amount of money in DnD currencies (pp, gp, ep, sp, cp), the bot will respond with that amount of money in all possible coins
        Example: `!money 2gp + 1ep`

        The following commands use dice notation like `(2d6 + 4)`. You can add and subtract as many amount of dice or normal numbers as you want in this notation. 
 
        !roll:
        Roll the given dice
        Example: `!roll 2d6 + 4`

        !analyse:
        Give statistics for a certain dice roll.
        Example: `!analyse 12 + 3d12 + 6` to see what range of max HP a level 4 fighter with +2 cons modifier could have
        Example: `!analyse graphs 12 + 3d12 + 6` add the word graphs or all to see some fancy chance distribution graphs aswell

        !chance:
        Compare 2 dice rolls to see which one is more likely to roll higher, or see how likely it is to roll a certain number (or higher/lower)
        Example: `!chance 2d6 > 1d12` (is a greatsword better then a greataxe)
        Example: `!chance 1d10 + 3 >= 8` (how likely is my eldritch blast to hit 8 or more)"""
        await message.channel.send(out)


client.run(discordToken)