import discord
from discord.ext import commands
from utils.csvreader import read_cricketers, read_teams, read_grounds
from models.player import Player
from models.team import Team
from models.venue import Stadium
import math
import asyncio
import time
import random

import numpy as np
from scipy.optimize import minimize
generic_commentary = {
    "W": [
        "He's gone! A big breakthrough!",
        "Clean bowled! That’s a huge moment!",
        "Edged and taken! Great bowling!",
        "Caught! That’s the end of him!",
        "Big appeal... and given! He’s out!",
        "Straight to the fielder! That’s out!",
        "What a delivery! He’s walked back in disbelief!",
        "Massive wicket! The bowler is ecstatic!",
        "That’s plumb! No doubt about it!",
        "Brilliant catch! The batter has to go!"
    ],
    ".": [
        "Dot ball. Building the pressure.",
        "Good tight bowling, no run.",
        "Straight to the fielder, no run.",
        "Well bowled, kept him quiet.",
        "That’s tidy from the bowler.",
        "No room to work with there.",
        "Dot ball! Frustration building.",
        "That one’s been defended solidly.",
        "Bowler will be happy with that.",
        "Batter not taking any risks."
    ],
    "1": [
        "Just a single, keeps the strike rotating.",
        "Worked into the gap for one.",
        "Smart cricket, just a single.",
        "Pushes it for an easy run.",
        "Good running, keeps the scoreboard ticking.",
        "Dabs it into the off-side, one run.",
        "Fielder cuts it off, just a single.",
        "Nice placement, but only a single.",
        "Comfortable single to rotate the strike.",
        "Takes it easy, just the one."
    ],
    "2": [
        "Good running, they come back for two.",
        "Pushed into the gap, easy two.",
        "Well-judged second run, good awareness.",
        "Smart placement, and they run two.",
        "Quick between the wickets, a couple more."
    ],
    "3": [
        "They’ll get three, great placement!",
        "Superb running! Three more to the total.",
        "Timed well, they’ll pick up three."
    ],
    "4": [
        "Cracked away for four!",
        "That’s a boundary! Lovely shot!",
        "Superb placement, four runs!",
        "Beats the fielder, races away!",
        "Shot! That’s four all the way!",
        "Driven beautifully to the fence!",
        "Finds the gap, that’s four!",
        "Elegant stroke, no stopping that!",
        "Timed to perfection, boundary!",
        "Too much width, punished for four!"
    ],
    "6": [
        "That’s massive! Six runs!",
        "What a hit! All the way for six!",
        "Clears the ropes comfortably!",
        "That’s into the stands! Six more!",
        "Tremendous power, huge six!",
        "Stand and deliver! Maximum!",
        "He’s got all of that one, six runs!",
        "Right from the middle of the bat!",
        "Huge hit! That’s out of here!",
        "High and handsome, six runs!"
    ]
}

dot_ball_commentary = {
    "very_fast_ball": [
        "Blazing pace, but well left!",
        "Absolute thunderbolt! No run.",
        "Beaten for pace! Great delivery.",
        "That flew past the bat!",
        "Too quick to handle!",
        "Pace and bounce, no shot offered.",
        "Lightning fast, but well defended.",
        "That zipped through! No run.",
        "Fiery delivery! Batter stays watchful.",
        "Sharp, skiddy, and past the bat!",
        "Fast and full, but no damage done.",
        "Scorcher! The batter just about survives."
    ],
    "swinging_ball": [
        "Oh, that moved a mile!",
        "Big swing, but well left.",
        "That’s hooping! No edge though.",
        "Shaped away beautifully!",
        "Massive in-swing, but blocked well.",
        "Late movement, but safely negotiated.",
        "That curved in sharply!",
        "A beauty! Just past the edge.",
        "Swinging dangerously! No contact.",
        "Great shape on that one!",
        "Hooped away! Beaten on the drive.",
        "That’s textbook swing bowling!"
    ],
    "slower_ball": [
        "Clever change of pace!",
        "Deceptive! The batter was early.",
        "Through him slowly—no timing.",
        "Great disguise! No run.",
        "Took all the pace off that.",
        "The batter read it late!",
        "Well bowled! No pace to work with.",
        "Rolled the fingers over it nicely.",
        "Tricked him! Straight to the fielder.",
        "Slower one does the job!",
        "Perfect off-cutter—dot ball!",
        "Smart variation from the bowler!"
    ],
    "seaming_ball": [
        "Nipped away sharply!",
        "Big seam movement, but no edge.",
        "That jagged back in sharply!",
        "Great seam position! Beaten again.",
        "Hit the seam and gripped!",
        "A jaffa! But no reward.",
        "Seamed a long way! Well played.",
        "That leapt off the deck!",
        "Unplayable movement! No run.",
        "The batter had no clue!",
        "A testing delivery—dot ball!",
        "Perfect line and length!"
    ],
    "high_bouncer": [
        "That climbed on him!",
        "Sharp bouncer, well evaded!",
        "He ducks under it—good leave.",
        "That was a nasty one!",
        "Short and sharp—no shot offered.",
        "Bouncer! The batter stays low.",
        "Steepling bounce! No attempt made.",
        "That rose suddenly! No run.",
        "Good bumper, but well judged.",
        "He sways away from danger.",
        "That zipped past his helmet!",
        "A fiery short ball—dot!"
    ],
    "spinning_ball": [
        "Big turn, but well watched!",
        "Oh, that gripped the surface!",
        "Huge rip, but safely played.",
        "Drift, dip, and no run!",
        "Classic off-spin—kept out.",
        "That spun sharply!",
        "Deceptive turn, but blocked well.",
        "Good drift, but no mistake.",
        "Massive turn! No edge though.",
        "Beaten in flight! No shot offered.",
        "That gripped and turned sharply!",
        "Tidy over from the spinner!"
    ],
    "bad_ball_pacer": [
        "Loose ball, but no run!",
        "That was a freebie—missed out!",
        "Short, wide, and straight to the fielder.",
        "Gift of a ball, but mistimed.",
        "Not the best, but still a dot.",
        "Half-tracker, but no timing!",
        "That should’ve gone for runs!",
        "A poor ball, but no damage.",
        "A rare loose one, but no run.",
        "Lucky escape for the bowler!",
        "Short and wide, but missed out.",
        "That was there to be hit!"
    ],
    "bad_ball_spinner": [
        "Dragged down, but no run!",
        "That was a free hit—missed!",
        "Full toss, but straight to the fielder.",
        "Loose ball, but batter mistimed it.",
        "Half-tracker, but no punishment.",
        "Not the best, but a dot ball.",
        "Batter missed a scoring chance!",
        "Lucky there, that was a poor ball.",
        "A real pie, but no runs!",
        "Bad delivery, but still a dot.",
        "That should’ve gone to the boundary!",
        "A rare bad one, but no harm done."
    ]
}

commentary = {
    "very_fast_ball": [
        "He's been absolutely blown away! That was sheer pace!",
        "Too quick, too good! The stumps are rattled!",
        "That was a thunderbolt! The batter had no chance!",
        "What a ripper! That’s 150 km/h straight through him!",
        "Lightning fast and straight as an arrow—gone!",
        "That’s express pace! The batter was beaten for speed!",
        "A rocket! Before he could react, the bails were gone!",
        "He just couldn’t keep up with that! Blazing speed!",
        "That's pure venom from the pacer! Crashed into the stumps!",
        "The batter was late on that one! Brutal pace!",
        "An absolute snorter! The sheer speed did him in!",
        "That is frighteningly quick! A wicket out of nowhere!"
    ],
    "swinging_ball": [
        "What a beauty! That swung a mile and took the top of off!",
        "Late swing, big trouble! That’s a masterclass in fast bowling!",
        "That’s textbook swing bowling! Pitched up and tailed in!",
        "It’s hooping around corners! Completely deceived him!",
        "A dream delivery for any bowler! The batter had no answer!",
        "That’s a banana swing! You don’t see many of those!",
        "Swung in, nipped away, and he’s gone! Perfect execution!",
        "Started well outside off and crashed into the stumps—unplayable!",
        "That’s a magnificent in-swinger! Shattered the stumps!",
        "An out-swinger with the perfect seam position—textbook dismissal!",
        "What a curve on that! The batter was completely outfoxed!",
        "The bowler is making the ball talk! That’s just magic!"
    ],
    "slower_ball": [
        "Deception at its best! The batter had no clue!",
        "He played way too early! That’s the perfect slower ball!",
        "Completely foxed him! That just dipped and took the stumps!",
        "The change of pace does the trick! Brilliant bowling!",
        "He was through the shot before the ball arrived—brilliant deception!",
        "Oh, that's a clever one! The batter was expecting pace and got none!",
        "That’s beautifully disguised! The batter didn’t pick it at all!",
        "Slower ball, big mistake, and he's gone! Smart bowling!",
        "Rolled his fingers over it, and the batter walked right into the trap!",
        "That’s patience and craft from the bowler—suckered him in!",
        "The batter had no idea that was coming—cleverly bowled!",
        "Perfectly disguised off-cutter! That was so well bowled!"
    ],
    "seaming_ball": [
        "That moved miles off the pitch! The batter stood no chance!",
        "The seam movement was unreal! Pitched on middle, hit off!",
        "An absolute ripper! Jagged back in and cleaned him up!",
        "That seamed away sharply and took the edge! Great bowling!",
        "The bowler found the perfect length, and the seam did the rest!",
        "That’s a jaffa! Moved off the deck and took the top of off!",
        "Landed on a crack, and that’s done all sorts of things!",
        "Sharp seam movement, and the batter is bamboozled!",
        "That’s unplayable! Off the deck and straight through!",
        "Hit the seam, straightened, and took out the off stump—classy!",
        "What a delivery! The batter expected straight, but it nipped away!",
        "That’s the magic of seam bowling! Perfect length, big movement!"
    ],
    "high_bouncer": [
        "That’s a nasty one! The batter had nowhere to go!",
        "Oh, that took off like a rocket! Brutal bouncer!",
        "That’s climbed on him and taken the edge! Great short ball!",
        "The batter was in two minds—duck or play? He chose wrong!",
        "A well-directed bumper, and it’s done the job!",
        "That’s vicious! It reared up and took him by surprise!",
        "What a brute of a ball! That nearly took his head off!",
        "Climbing, searing bouncer, and he's gloved it to the keeper!",
        "That’s why you bowl short—rushed the batter into a mistake!",
        "Banged in hard, kicked up off a length, and the batter is gone!",
        "That’s a mean delivery! He had no idea where that was going!",
        "That is chin music at its best! Classic fast bowling!"
    ],
    "spinning_ball": [
        "That’s turned a mile! The batter was completely done in!",
        "What a ripper! Classic off-spin, drew him forward and turned past him!",
        "That’s a magician at work! Big spin and gone!",
        "The ball gripped, spun sharply, and sent him packing!",
        "That’s the perfect leg-break! Drifted in, spun away, and took the top of off!",
        "Massive turn off the pitch! That’s an absolute beauty!",
        "He had no clue! The ball spun right past his bat!",
        "That’s vintage spin bowling! Got him playing down the wrong line!",
        "What a delivery! Spun a mile and hit the stumps!",
        "Flight, dip, and turn—textbook spin bowling!",
        "That’s a peach! Drifted in and spat off the surface!",
        "Unplayable turn and bounce! The batter was all at sea!"
    ],
    "bad_ball_pacer": [
        "That’s a terrible ball, but he’s still managed to get a wicket!",
        "Oh, that was short, wide, and asking to be hit—but he’s edged it!",
        "That’s a gift for the batter, but he’s thrown it away!",
        "A nothing delivery, but the batter has found a way to get out!",
        "That’s a half-tracker, and somehow he’s holed out!",
        "That’s a full toss, and he’s smashed it straight to the fielder!",
        "That’s a real loosener, but he’s still got a wicket!",
        "An absolute pie, but the batter has served it straight to the fielder!",
        "The bowler won’t believe his luck—that was a rank delivery!",
        "That was there to be hit, but the batter made a mess of it!",
        "That’s not a wicket-taking ball, but the batter has gifted it!",
        "That’s a buffet ball, but he’s just helped himself to an easy dismissal!"
    ],
    "bad_ball_spinner": [
        "That was a shocking delivery, but it’s still got a wicket!",
        "An absolute drag-down, and he’s somehow picked out the fielder!",
        "That was begging to be hit, but the batter has thrown it away!",
        "A real long-hop, but he’s mistimed it straight to hand!",
        "That’s a terrible ball, but the batter has managed to get himself out!",
        "That’s a juicy full toss, and he’s chipped it to mid-on!",
        "The bowler won’t be proud of that, but a wicket is a wicket!",
        "That was there for the taking, but the batter has misjudged it!",
        "An absolute gift, but he’s hit it straight to the fielder!",
        "That’s the worst delivery of the day, and it’s got a wicket!",
        "A dreadful delivery, but the batter has made an even bigger mistake!",
        "That’s a rank half-tracker, but somehow it’s done the job!"
    ]
}
single_commentary = {
    "very_fast_ball": [
        "Quick single! Sharp running.",
        "Worked away, just one.",
        "Tapped and run—good awareness!",
        "Fast and full, nudged for one.",
        "Pushed into the gap, easy single.",
        "Smart rotation of strike!",
        "Quick hands, quick feet—single taken.",
        "Dabbed down, off the mark!",
        "Soft hands, single to third man.",
        "Punched to mid-off, quick run!",
        "They scamper through for one!",
        "Good hustle, keeps the scoreboard ticking."
    ],
    "swinging_ball": [
        "Glanced away, one run.",
        "Nicely tucked off the pads.",
        "Clipped into the leg side, easy run.",
        "Soft hands, played with control.",
        "Steered behind square for a single.",
        "Shaped away, but guided for one.",
        "Late swing, but placed nicely for a run.",
        "Worked with the swing, single taken.",
        "Let the ball do the work, just a single.",
        "Off the inside edge, safely taken!",
        "Beaten in the air, but gets one!",
        "Smart placement, strike rotated."
    ],
    "slower_ball": [
        "Waited for it, guided for one.",
        "Soft hands, easy single.",
        "Well-disguised slower one, nudged away.",
        "Pushed into the off-side, quick run.",
        "Read the change of pace well.",
        "Good cricket, keeps the scoreboard moving.",
        "Timed well, just one.",
        "Used the pace, down to third man.",
        "Dabbed into the gap, easy run.",
        "Rotates strike with a gentle push.",
        "Clever batting, found the gap!",
        "Nice little single there!"
    ],
    "seaming_ball": [
        "Edged, but safe—single taken.",
        "Inside edge, but no danger!",
        "Worked away, one more to the total.",
        "Nice use of the seam, guided for one.",
        "Soft hands, good awareness.",
        "Tucked off the hip, easy single.",
        "Nudged to square leg, well run.",
        "Seam movement, but played late for one.",
        "Off the thick edge, single taken!",
        "Safe shot, strike rotated.",
        "Good running, keeps the pressure on.",
        "Glanced fine, just a single!"
    ],
    "high_bouncer": [
        "Pulled away, but just a single.",
        "Rode the bounce well, easy run.",
        "Dug out, scampered through for one!",
        "Defensive push, quick single taken.",
        "Soft hands, well placed.",
        "Controlled pull shot, single added.",
        "Handled the bounce well, run taken.",
        "Fended off, but they sneak a run!",
        "Worked off the body, single to leg.",
        "Hooked safely, just a run.",
        "Taps it down, keeps the strike.",
        "Bouncer negotiated, strike rotated."
    ],
    "spinning_ball": [
        "Neatly worked away for one.",
        "Good use of the feet, just a run.",
        "Turn and bounce, but safely played.",
        "Quick single! Good awareness.",
        "Swept away, but just a single.",
        "Soft hands, no risk there.",
        "Dabbed to point, well judged run.",
        "Flighted ball, gently worked for one.",
        "Just a nudge, but enough for a run.",
        "Steered into the gap, easy run.",
        "Timed well, no risk single.",
        "Smart batting, keeps the scoreboard ticking."
    ],
    "bad_ball_pacer": [
        "Loose delivery, but only a single.",
        "Short and wide, but just one run.",
        "Sloppy ball, but no real damage.",
        "Half-tracker, but fielded well.",
        "Mistimed shot, only a single.",
        "Lucky escape for the bowler, just one.",
        "Full toss, but straight to the fielder!",
        "Short ball, but only a single taken.",
        "Gift of a ball, but batter misses out.",
        "Batter could’ve done more with that one!",
        "A rare bad ball, but just a single.",
        "Pushed away, strike rotated."
    ],
    "bad_ball_spinner": [
        "Poor ball, but no real punishment.",
        "Dragged down, but just one run.",
        "Full toss, but straight to the fielder!",
        "Loose delivery, only a single taken.",
        "Half-tracker, but no power in the shot.",
        "Missed opportunity for more runs.",
        "Flighted too much, but just a single.",
        "Not the best, but gets away with it!",
        "Could’ve gone for more, just a single.",
        "Short and wide, but well fielded.",
        "Bad ball, but batter mistimed it.",
        "A let-off for the bowler!"
    ]
}

two_commentary = {
    "very_fast_ball": [
        "Driven hard, they push for two!",
        "Quick hands, well-placed—two runs.",
        "Worked into the gap, good running!",
        "Punched off the back foot, easy two.",
        "Hustled back, great running!"
    ],
    "swinging_ball": [
        "Flicked off the pads, two more!",
        "Late swing, but placed well for a couple.",
        "Nicely timed, enough for two.",
        "Worked square, turning for the second!",
        "Fine placement, easy two runs."
    ],
    "slower_ball": [
        "Waited on it, placed well for two!",
        "Soft hands, good running for a couple.",
        "Deft touch, they come back for two.",
        "Slower one, but guided into space—two!",
        "Played late, enough time for two."
    ],
    "seaming_ball": [
        "Thick edge, but safe—two runs!",
        "Worked into the deep, coming back for two.",
        "Nice placement, well-run couple!",
        "Tucked behind square, good running.",
        "Beats the infield, easy two!"
    ],
    "high_bouncer": [
        "Pulled away, they push for two!",
        "Controlled shot, enough time for a couple.",
        "Hooked, but no full connection—just two.",
        "Rode the bounce, played well for two!",
        "Nicely placed, hustled back for the second."
    ],
    "spinning_ball": [
        "Swept fine, they'll get two!",
        "Quick footwork, placed well—two runs.",
        "Flighted delivery, nudged into space—two!",
        "Played with soft hands, coming back for two.",
        "Well-judged shot, comfortably two!"
    ],
    "bad_ball_pacer": [
        "Poor ball, but just two runs.",
        "Misfield! Allows them to come back for two.",
        "Full toss, but no big damage—just a couple.",
        "Short and wide, but straight to the fielder—two runs.",
        "Not punished fully, but they run two."
    ],
    "bad_ball_spinner": [
        "Dragged down, but only two runs.",
        "Misfield lets them take an extra run!",
        "Flighted poorly, but well fielded—two.",
        "Half-tracker, but batter mistimes—two runs.",
        "Short and wide, but straight to the fielder—just two."
    ]
}

three_commentary = {
    "very_fast_ball": [
        "Drilled through the gap, three runs!",
        "Timed beautifully, they’ll get three.",
        "Great placement! Three more added."
    ],
    "swinging_ball": [
        "Worked off the pads, racing away—three!",
        "Lovely flick, they'll run three!",
        "Using the swing, into the gap—three runs!"
    ],
    "slower_ball": [
        "Waited for it, placed well—three runs!",
        "Great placement, good running for three.",
        "Soft hands, into the deep—three more!"
    ],
    "seaming_ball": [
        "Beats the infield, they'll get three!",
        "Nice placement, hard running—three added.",
        "Worked behind square, turning for the third!"
    ],
    "high_bouncer": [
        "Hooked away! Good running, they get three.",
        "Controlled shot, finds space—three runs.",
        "Pulled hard, just short of the rope—three!"
    ],
    "spinning_ball": [
        "Swept fine, they'll come back for three!",
        "Great use of the feet, lofted for three runs.",
        "Timed well, deep fielder cuts it off—three!"
    ],
    "bad_ball_pacer": [
        "Loose delivery, but only three runs.",
        "Bad ball, but not fully punished—three runs.",
        "Sloppy bowling, but just three added."
    ],
    "bad_ball_spinner": [
        "Dragged down, but only three runs.",
        "Short and wide, but straight to the fielder—three runs.",
        "Not a great ball, but just three runs taken."
    ]
}
four_commentary = {
    "very_fast_ball": [
        "Blazing drive, races to the fence!",
        "Too fast, too straight—four runs!",
        "Cracked off the back foot, bullet to the boundary!",
        "Edged! Flies past slip for four.",
        "Short and wide, cut away with ease—four runs!",
        "Thunderous pull! No chance for the fielder.",
        "Pure timing! Races to the rope.",
        "Blistering shot! Just a blur to the boundary.",
        "Driven on the up, screaming to the fence!",
        "Lightning-fast hands! That's four in a flash.",
        "Pace on, pace off the bat—four more!",
        "What a shot! The crowd loved that one."
    ],
    "swinging_ball": [
        "Beautifully timed through midwicket—four!",
        "Late swing, but glanced fine—four more!",
        "Lovely wrist work! Beats the fielder, four runs.",
        "Pitched up and driven gloriously for four!",
        "Swinging in, but clipped away neatly—four!",
        "Edges but no slip in place—four runs!",
        "Exquisite cover drive! Right out of the textbook.",
        "Used the swing, guided past point—four more.",
        "Overpitched and punished—four runs!",
        "Wristy flick, races past midwicket—four!",
        "Plays it late, threading the gap—four!",
        "No need to run, that’s four from the moment it left the bat."
    ],
    "slower_ball": [
        "Waited on it, lofted over cover—four!",
        "Smart batting! Finds the gap for four.",
        "Deft touch! Just wide of slip for four.",
        "Short and sat up, crunched for four!",
        "Took his time, picked his spot—four runs!",
        "Clever placement! Fielder watches it roll to the fence.",
        "Great use of the feet, lifts it for four.",
        "Read it early, carved past point—four runs!",
        "Fooled by the pace but still finds the boundary!",
        "Full toss, and that’s four easy runs.",
        "Perfectly weighted push—beats the field for four.",
        "Patience rewarded! Pounces on the slower ball for four."
    ],
    "seaming_ball": [
        "Edge and four! Soft hands save him.",
        "Cracked past gully! Four runs.",
        "Width on offer, slashed away for four!",
        "Seamed away, but steered with precision—four!",
        "Takes the edge, but races away for four!",
        "Just wide of the fielder! Four runs.",
        "Uses the angle, slices past point—four!",
        "Bit of movement, but caressed through covers—four!",
        "Beats the infield, quick outfield helps—four more.",
        "Delicate touch, guides it past slip for four.",
        "Seamed back in, but flicked beautifully—four runs!",
        "Crashes through cover! Stunning shot."
    ],
    "high_bouncer": [
        "Hooked away! No stopping that—four!",
        "Pulled with authority! Four runs.",
        "Short, sat up, and dispatched for four!",
        "Rocked back and smashed through midwicket—four!",
        "Brave shot! Uppercut for four over slip!",
        "Rode the bounce, guided to the ropes—four!",
        "Hooked cleanly, fielder just a spectator—four!",
        "Pulled hard! One bounce into the fence.",
        "Short and wide, free shot for four!",
        "Great control on the bounce, that’s four.",
        "Pulled away disdainfully! Too easy.",
        "Brilliant shot! Clears the infield for four."
    ],
    "spinning_ball": [
        "Swept fine, beats the fielder—four!",
        "Dances down, lofts it beautifully—four runs!",
        "Waited for it, cut away past point—four!",
        "Timed to perfection, splits the gap—four!",
        "Well flighted, but punished—four more!",
        "Exquisite placement, nudged for four.",
        "Reverse sweep! Finds the fence.",
        "Flighted up, but driven with class—four runs!",
        "Powerful shot! Beats mid-off to the boundary.",
        "Loopy delivery, smashed through covers—four!",
        "Late cut, so fine the keeper barely moved—four!",
        "Masterful stroke! Four more added to the total."
    ],
    "bad_ball_pacer": [
        "Poor line, punished for four!",
        "Rank full toss, helped to the fence.",
        "Short and wide, freebie four runs!",
        "No discipline there, four easy runs.",
        "Loose delivery, batter says thank you—four more!",
        "Gift-wrapped boundary, easy pickings!",
        "Wayward ball, crashes into the rope—four runs!",
        "Over-pitched and dispatched—four!",
        "Not what the bowler wanted, but four runs it is.",
        "Too much width, carved away for four.",
        "Not good enough at this level—four more!",
        "Batter helps himself to a free boundary."
    ],
    "bad_ball_spinner": [
        "Dragged down, hammered for four!",
        "Half-tracker, no mercy—four runs!",
        "Loose ball, and that’s four more.",
        "Short, wide, and absolutely punished!",
        "Bowler will want that one back—four runs!",
        "Tossed up poorly, batter cashes in for four.",
        "Easily dispatched, straight to the ropes!",
        "Not a good ball, easy boundary.",
        "Rank bad delivery, batter takes full advantage—four!",
        "Too much air, drilled for four!",
        "Short and asking to be hit—four runs!",
        "That’s a freebie, and the batter doesn’t miss out!"
    ]
}

six_commentary = {
    "very_fast_ball": [
        "Boom! That’s out of the park!",
        "What a strike! Sends it soaring over the ropes!",
        "Pace on, but he’s just launched it for six!",
        "Crushed! That’s a monster hit!",
        "Lightning-fast delivery, but even faster hands—six runs!",
        "Pure power! That’s gone into the stands!",
        "Absolutely smoked! A six to remember!",
        "Short, quick, and destroyed—six more!",
        "That’s a rocket off the bat! Maximum!",
        "Pace or no pace, this batter is unstoppable—six!",
        "Clears the boundary with ease! What a hit!",
        "No half-measures there! That’s six all the way!"
    ],
    "swinging_ball": [
        "Picks the swing early and sends it sailing—six!",
        "Glorious lofted drive! That’s huge!",
        "Got underneath it, and it keeps traveling—six runs!",
        "Late swing, but dispatched over long-off!",
        "What a shot! Plays with the swing and goes the distance!",
        "Edges it… and it carries for six! Unbelievable!",
        "Textbook timing! Six runs over extra cover.",
        "Saw the swing, adjusted, and lifted it beautifully—six!",
        "Controlled hit, maximum result!",
        "Just a flick of the wrists, and it’s six more!",
        "Wow! That’s all about balance and timing!",
        "Picked the slower swing perfectly—six!"
    ],
    "slower_ball": [
        "Waited for it, and launched it into the crowd!",
        "Read the pace and smashed it miles!",
        "Slower ball, but he’s picked it perfectly—six!",
        "That’s patience rewarded! Waited, and sent it packing!",
        "Oh, that’s a towering hit! Six runs!",
        "Took his time and still got all of it—maximum!",
        "Gave himself room, and that’s gone out of the stadium!",
        "Fooled for a moment, but the end result is six!",
        "What a shot! Straight as an arrow for six!",
        "Saw it, measured it, and demolished it—six more!",
        "Not enough deception on that one—six runs!",
        "Holds his shape, and sends it soaring!"
    ],
    "seaming_ball": [
        "Edges it... and it goes all the way! Six runs!",
        "Took on the challenge, and it’s a beauty—six!",
        "Seamed away, but still launched over the boundary!",
        "Timed to perfection! That’s a big six!",
        "Brave shot! Clears the rope comfortably.",
        "Seam movement? No problem! Deposited for six.",
        "Length ball, and he’s absolutely nailed it!",
        "Wasn’t an easy shot, but he’s made it look effortless!",
        "That’s gone miles! A massive six!",
        "Adjusts late, but gets enough on it—six more!",
        "Pure class! Makes seam movement look meaningless.",
        "Brute force! That’s over the sight screen!"
    ],
    "high_bouncer": [
        "Hooked with authority! That’s a huge six!",
        "Short, sat up, and absolutely hammered—six!",
        "Pulled high, pulled long—six runs!",
        "Uppercut over third man! Spectacular shot!",
        "That’s into the stands! Tremendous power!",
        "Rocked back and launched into the night sky!",
        "Bouncer? No problem! Six more!",
        "Took on the short ball and won—maximum!",
        "What a fearless shot! Six over fine leg!",
        "Not intimidated by the bounce—massive hit!",
        "A stunning hook shot! All the way for six!",
        "Takes it early, and it sails away!"
    ],
    "spinning_ball": [
        "Stepped out and thumped it for six!",
        "Dances down, and it’s into the second tier!",
        "Spin or no spin, that’s gone a long way!",
        "What a clean strike! Straight over the bowler!",
        "Lofted drive, and it’s disappeared!",
        "Just enough elevation, and it clears the ropes!",
        "Took it on, and it’s a towering six!",
        "Tossed up, and it’s been dealt with!",
        "Superb footwork! Maximum!",
        "Reverse sweep for six! Outrageous shot!",
        "Spinner under pressure now—six more!",
        "Reads the turn and sends it over long-on!"
    ],
    "bad_ball_pacer": [
        "Full toss and punished! That’s a massive six!",
        "A gift, and the batter says thank you—six more!",
        "Rank short ball, pulled over deep square!",
        "Poor delivery, and that’s sailing over the ropes!",
        "Misses the yorker, and it’s out of the ground!",
        "Bowler loses control, batter takes full advantage—six!",
        "Oh dear, that’s too easy! Maximum!",
        "All the time in the world, and he nails it!",
        "Way too short, and he’s just dismissed it!",
        "Horrible ball, magnificent shot!",
        "That’s a freebie, and he’s cashed in—six runs!",
        "Bowl that at this level, and you’ll be punished!"
    ],
    "bad_ball_spinner": [
        "Half-tracker, and it’s disappeared!",
        "That’s a shocker! Clubbed over long-on!",
        "Full toss, and that’s not coming back!",
        "Spinner won’t want to see that one again—six runs!",
        "Flighted poorly, and it’s been demolished!",
        "Rank bad ball, and the batter says ‘thank you’!",
        "You cannot bowl there! Dispatched!",
        "Horrible length, and he takes full toll—six!",
        "Short, wide, and absolutely launched!",
        "That’s way too easy! Six more!",
        "Bowler shaking his head—he knows that was poor!",
        "A real loosener, and it’s been put away!"
    ]
}

