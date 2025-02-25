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



# Load data from CSV files
players = read_cricketers('data/players.csv')
teams = read_teams('data/teams.csv', players)
grounds = read_grounds('data/venues.csv')


#  up the bot with a command prefix
# Create an instance of Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Initialize the bot with the intents
bot = commands.Bot(command_prefix="!", intents=intents)

import math

def calculate_revenue(format, fanbase_team1, fanbase_team2, player_followers, tournament_profile, closeness, runs_scored, stadium_quality, stadium_capacity):
    """
    Calculate cricket match revenue split by ticket sales and broadcast rights.
    
    Args:
        format (str): Match format ('T20', 'ODI', 'Test').
        fanbase_team1 (int): Fanbase of team 1 in millions.
        fanbase_team2 (int): Fanbase of team 2 in millions.
        player_followers (list): Instagram followers of each player in millions.
        tournament_profile (int): Tournament importance (1 to 5).
        closeness (float): Match competitiveness (0 to 1).
        runs_scored (int): Total runs scored.
        stadium_quality (int): Stadium quality rating (1 to 10).
        stadium_capacity (int): Stadium capacity (number of seats).
    
    Returns:
        tuple: (broadcast_revenue, ticket_revenue) in dollars.
    """
    # Define format multipliers
    format_multipliers = {'T20': 1.2, 'ODI': 1.0, 'Test': 0.8}
    if format not in format_multipliers:
        raise ValueError("Invalid format. Use 'T20', 'ODI', or 'Test'.")
    
    # Calculate total fanbases
    team_fanbase = fanbase_team1 + fanbase_team2
    player_fanbase = player_followers
    
    # Calculate attractiveness score
    A = (team_fanbase / 100) * (player_fanbase / 50)**0.5 * tournament_profile * \
        format_multipliers[format] * (closeness / 0.5)**0.5 * (runs_scored / 300)**0.2 * \
        (stadium_quality / 5)**0.3
    
    # Calculate broadcast revenue
    broadcast_revenue = 10_000_0 * A
    
    # Calculate ticket revenue
    occupancy_rate = 1 - math.exp(-1.609 * A)
    ticket_revenue = stadium_capacity * 25 * occupancy_rate
    
    return broadcast_revenue, ticket_revenue

       
def display_scorecard(batting_stats, bowling_stats, team_name, score, wickets, detailed_overs):
    """Display the scorecard for a team with enhanced details."""

    overs_completed = len(detailed_overs) // 6
    balls_in_current_over = len(detailed_overs) % 6
    current_over = f"{overs_completed}.{balls_in_current_over}"
    message = ""
    message += (f"{team_name} {score}/{wickets} ({current_over})")
    
    message += ("\nBatting:\n")
    message += ("Batter           Runs  Balls  SR\n")
    message += ("-" * 35)
    for player, stats in batting_stats.items():
        if stats['balls'] > 0:  # Only show batsmen who faced deliveries
            strike_rate = (stats['runs'] * 100) / stats['balls']
            status = "*" if not stats['out'] else ""
            message += (f"{player:<15} {stats['runs']}{status:<5} {stats['balls']:<6} {strike_rate:>5.1f}\n")

    message += ("\nBowling:\n")
    message += ("Bowler           O    R    W    Econ\n")
    message += ("-" * 40)
    for player, stats in bowling_stats.items():
        if stats['overs'] > 0:  # Only show bowlers who bowled
            economy = stats['runs'] / stats['overs'] if stats['overs'] > 0 else 0
            message += (f"{player:<15} {stats['overs']:<4} {stats['runs']:<4} {stats['wickets']:<4} {economy:>5.1f}\n")


    print(message)

    if False:
        print(f"\nBall by Ball with Overs for {team_name}:")
        
        current_score = 0
        current_wickets = 0
        
        # Initialize batsmen
        batsmen = list(batting_stats.keys())
        striker = batsmen[0]
        non_striker = batsmen[1]
        batsmen_scores = {name: {'runs': 0, 'balls': 0} for name in batting_stats}
        
        # Initialize bowling_stats for all bowlers to zero
        bowlers = set(ball.split()[0] for ball in detailed_overs)
        for bowler in bowlers:
            bowling_stats[bowler] = {'overs': 0, 'runs': 0, 'wickets': 0}
        
        # Process balls over by over
        total_balls = len(detailed_overs)
        for i in range(0, total_balls, 6):
            over_num = i // 6
            over_balls = detailed_overs[i:min(i+6, total_balls)]
            bowler = over_balls[0].split()[0]
            
            print(f"\nOver {over_num + 1}:")
            over_runs = 0
            over_wickets = 0
            
            # Process each ball in the over
            for ball_num, ball in enumerate(over_balls, 1):
                print(f"  {over_num}.{ball_num}: {ball}")
                
                if "OUT" in ball:
                    over_wickets += 1
                    current_wickets += 1
                    batsmen_scores[striker]['balls'] += 1
                    if current_wickets < len(batsmen) - 1:
                        striker = batsmen[current_wickets + 1]
                else:
                    runs = int(ball.split()[-2])
                    over_runs += runs
                    current_score += runs
                    batsmen_scores[striker]['runs'] += runs
                    batsmen_scores[striker]['balls'] += 1
                    if runs % 2 == 1:
                        striker, non_striker = non_striker, striker
            
            # Rotate strike at end of over
            striker, non_striker = non_striker, striker
            
            # Update bowling figures
            bowling_stats[bowler]['overs'] += 1
            bowling_stats[bowler]['runs'] += over_runs
            bowling_stats[bowler]['wickets'] += over_wickets
            
            # Print single-line summary after each over
            striker_stats = f"{striker}: {batsmen_scores[striker]['runs']}*({batsmen_scores[striker]['balls']})"
            non_striker_stats = f"{non_striker}: {batsmen_scores[non_striker]['runs']}({batsmen_scores[non_striker]['balls']})"
            bowler_stats = f"{bowler}: {over_runs}/{over_wickets} ({bowling_stats[bowler]['overs']}--{bowling_stats[bowler]['runs']}-{bowling_stats[bowler]['wickets']})"
            
            print(f"Score: {current_score}/{current_wickets} | {striker_stats}, {non_striker_stats} | {bowler_stats}")
        
    


def display_scorecard_discord(team_name, batting_stats, bowling_stats):
    """Display formatted batting and bowling scorecards"""
    # Create batting scorecard
    batting_card = f"**{team_name} Batting**\n```\n"
    batting_card += "Batter          Runs  Balls  SR\n"
    batting_card += "-" * 35 + "\n"
    
    for player, stats in batting_stats.items():
        strike_rate = (stats["runs"] / stats["balls"] * 100) if stats["balls"] > 0 else 0
        not_out = "" if stats["out"] else "*"
        batting_card += f"{player:<15} {stats['runs']:<5}{not_out} {stats['balls']:<6} {strike_rate:.2f}\n"
    
    batting_card += "```"
    print(batting_card)

    # Create bowling scorecard
    bowling_card = f"**{team_name} Bowling**\n```\n"
    bowling_card += "Bowler          O    M    R    W    Econ\n"
    bowling_card += "-" * 45 + "\n"
    
    for player, stats in bowling_stats.items():
        if stats["overs"] > 0:  # Only show bowlers who bowled
            economy = stats["runs"] / stats["overs"] if stats["overs"] > 0 else 0
            bowling_card += f"{player:<15} {stats['overs']:<4}  {stats['runs']:<4} {stats['wickets']:<4} {economy:.2f}\n"
    
    bowling_card += "```"
    print(bowling_card)



def play_match(team1name: str, team2name: str, venuename: str, format: str):
    """
    Command to start a match simulation.
    Loads teams, venue, and match format, then calls the match simulation logic.
    """
    print(f"Match Between {team1name} & {team2name}")
    players = read_cricketers("data/players.csv")
    grounds = read_grounds("data/venues.csv")
    teams = read_teams("data/teams.csv", players)
    teams = read_teams('data/teams.csv', players)
    print(f"Loaded teams: {[team.name for team in teams]}")
    print(f"Loaded grounds: {[ground.name for ground in grounds]}")
    # Find the requested teams
    team1 = next((team for team in teams if team.name.lower() == team1name.lower()), None)
    team2 = next((team for team in teams if team.name.lower() == team2name.lower()), None)
    
    # Find the requested ground
    ground = next((g for g in grounds if g.name.lower() == venuename.lower()), None)

    # Valnameate inputs
    if not team1:
        print(f"Team '{team1name}' not found!")
        return
    if not team2:
        print(f"Team '{team2name}' not found!")
        return
    if not ground:
        print(f"Ground '{venuename}' not found!")
        return
    if format.lower() not in ["test", "odi", "t20"]:
        print("Invalname match format! Choose from: Test, ODI, T20.")
        return

    # Confirm match setup
    print(f"Starting {format.upper()} match between {team1.name} and {team2.name} at {ground.name}!")

    for player in team1.players: 
        player.set_match_fitness()
    for player in team2.players: 
        player.set_match_fitness()

    # Placeholder for match simulation logic
    # TODO: Implement the match simulation logic
    print(team1.players)
    print(team2.players)
    assert len(team1.players) == 11 and len(team2.players) == 11
    if format.upper() == "ODI": 
        simulate_odi(team1, team2, ground)
    if format.lower() == "test":
        simulate_test(team1,team2, ground)
    if format.upper() == "T20":
        simulate_t20(team1,team2, ground)



import math
import math

def calculate_aggression_t20(over, pitch, target, striker, non_striker, settled_striker, settled_non_striker):
    """
    Determines the appropriate aggression level (target RPO) for an ODI innings continuously.

    Parameters:
    - over (int): The current over number.
    - pitch (dict): A dictionary containing pitch conditions (pace, turn, bounce, grass_cover).
    - target (int or None): The target score (None if batting first).
    - striker (player object): The striker with attributes like odi_ave and odi_sr.
    - non_striker (player object): The non-striker with attributes like odi_ave and odi_sr.
    - settled_striker (float): The settled meter value of the striker (0 to 10).
    - settled_non_striker (float): The settled meter value of the non-striker (0 to 10).

    Returns:
    - float: The recommended aggression level as target_rpo.
    """
    # Step 1: Calculate base RPO based on over (baseline)
    base_rpo = 4  # Standard ODI base RPO
    if over < 6:
        base_rpo += 4 * math.log(over + 1, 2.7)  # Powerplay: aggressive start
    elif over < 14:
        base_rpo += 1.2 * 3.7 ** ((over - 6) / 25)  # Middle overs: steady increase
    else:
        base_rpo += 2 * (over - 35) / 100 + 2.7 ** ((over - 15) / 8)  # Death overs: sharp rise


    # Step 3: Target chasing adjustment
    if target is not None and over < 50:
        rpo_needed = target / (50 - over)
        target_factor = 1 + (1 / (1 + math.exp(-0.5 * (rpo_needed - base_rpo)))) - 0.5
        base_rpo *= target_factor
    else:
        rpo_needed = base_rpo + 1
    # Step 8: Apply pitch factor
    target_rpo = (rpo_needed * base_rpo) ** 0.5

    # Step 9: Ensure RPO is between 4 and 12
    target_rpo = max(3, min(target_rpo, 15))

    return base_rpo/9


def calculate_aggression_odi(over, pitch, target, striker, non_striker, settled_striker, settled_non_striker):
    """
    Determines the appropriate aggression level (target RPO) for an ODI innings continuously.

    Parameters:
    - over (int): The current over number.
    - pitch (dict): A dictionary containing pitch conditions (pace, turn, bounce, grass_cover).
    - target (int or None): The target score (None if batting first).
    - striker (player object): The striker with attributes like odi_ave and odi_sr.
    - non_striker (player object): The non-striker with attributes like odi_ave and odi_sr.
    - settled_striker (float): The settled meter value of the striker (0 to 10).
    - settled_non_striker (float): The settled meter value of the non-striker (0 to 10).

    Returns:
    - float: The recommended aggression level as target_rpo.
    """
    # Step 1: Calculate base RPO based on over (baseline)
    base_rpo = 4  # Standard ODI base RPO
    if over < 10:
        base_rpo += 2 * math.log(over + 1, 2.7)  # Powerplay: aggressive start
    elif over < 35:
        base_rpo += 1 * 2.7 ** ((over - 10) / 25)  # Middle overs: steady increase
    else:
        base_rpo += 1.5 * (over - 35) / 100 + 2.7 ** ((over - 35) / 8)  # Death overs: sharp rise


    # Step 3: Target chasing adjustment
    if target is not None and over < 50:
        rpo_needed = target / (50 - over)
        target_factor = 1 + (1 / (1 + math.exp(-0.5 * (rpo_needed - base_rpo)))) - 0.5
        base_rpo *= target_factor
    else:
        rpo_needed = base_rpo + 1





    # Step 8: Apply pitch factor
    target_rpo = (rpo_needed * base_rpo) ** 0.5

    # Step 9: Ensure RPO is between 4 and 12
    target_rpo = max(3, min(target_rpo, 15))

    return target_rpo/7


def simulate_test(team1, team2, venue):
    """Simulate a Test match between two teams, including follow-ons."""

    # Random toss to decide who bats first
    if random.randint(1, 100) > 100:
        team1, team2 = team2, team1

    pitch = venue

    # Simulate first innings of team1
    team1_score1, team1_wickets1, team1_batting_stats1, team1_bowling_stats1 = simulate_test_innings(team1, team2, pitch)

    # Display scorecard for team 1 (first innings)
    display_scorecard(team1_batting_stats1, team1_bowling_stats1, team1.name, team1_score1, team1_wickets1, "1st Innings")

    # Simulate first innings of team2
    team2_score1, team2_wickets1, team2_batting_stats1, team2_bowling_stats1 = simulate_test_innings(team2, team1, pitch)

    # Display scorecard for team 2 (first innings)
    display_scorecard(team2_batting_stats1, team2_bowling_stats1, team2.name, team2_score1, team2_wickets1, "1st Innings")

    # Follow-on logic
    follow_on = False
    if team1_score1 > team2_score1 and team1_score1 - team2_score1 >= 200:
        print(f"\n{team2.name} is asked to follow on.")
        follow_on = True
        team2_score2, team2_wickets2, team2_batting_stats2, team2_bowling_stats2 = simulate_test_innings(team2, team1, pitch)
        display_scorecard(team2_batting_stats2, team2_bowling_stats2, team2.name, team2_score2, team2_wickets2, "2nd Innings (Follow-on)")
        team1_score2, team1_wickets2, team1_batting_stats2, team1_bowling_stats2 = simulate_test_innings(team1, team2, pitch, target = team2_score1 + team2_score2)
        display_scorecard(team1_batting_stats2, team1_bowling_stats2, team1.name, team1_score2, team1_wickets2, "2nd Innings")

    else:
        # Simulate second innings of team1
        team1_score2, team1_wickets2, team1_batting_stats2, team1_bowling_stats2 = simulate_test_innings(team1, team2, pitch)
        display_scorecard(team1_batting_stats2, team1_bowling_stats2, team1.name, team1_score2, team1_wickets2, "2nd Innings")

        # Simulate second innings of team2
        team2_score2, team2_wickets2, team2_batting_stats2, team2_bowling_stats2 = simulate_test_innings(team2, team1, pitch, target=team1_score1 + team1_score2)
        display_scorecard(team2_batting_stats2, team2_bowling_stats2, team2.name, team2_score2, team2_wickets2, "2nd Innings")

    # Determine winner
    total_team1_score = team1_score1 + team1_score2
    total_team2_score = team2_score1 + (team2_score2 if follow_on or team2_score2 is not None else 0)

    if total_team1_score > total_team2_score:
        print(f"\n{team1.name} wins by {total_team1_score - total_team2_score} runs!")
    elif total_team2_score > total_team1_score:
        if team1_wickets2 == 10:
            print(f"\n{team2.name} wins by an innings and {total_team2_score - total_team1_score} runs!")
        else:
            print(f"\n{team2.name} wins by {10 - team2_wickets2} wickets!")
    else:
        print("\nMatch drawn!")


def get_ball_probabilities_test(expected_runs):
    """
    Calculates a distribution of weights for runs (0, 1, 2, 3, 4, 6) 
    that result in the given expected runs, based on a scaled distribution.

    Args:
        expected_runs (float): The target expected runs.
        striker (bool): A boolean representing whether the batter is a striker (not used in this simplified version).

    Returns:
        numpy.ndarray: An array of probabilities for runs (0, 1, 2, 3, 4, 6).
    """

    runs = np.array([0, 1, 2, 3, 4, 6])
    base_probs = np.array([0.8, 0.12, 0.02, 0.01, 0.04, 0.01])

    def calculate_expected(probs):
        return np.sum(runs * probs)

    def error(scaling_factor):
        scaled_probs = base_probs * scaling_factor
        scaled_probs /= np.sum(scaled_probs)  # Normalize
        return abs(calculate_expected(scaled_probs) - expected_runs)

    result = minimize(error, 1.0, bounds=[(0, None)]) # find the scaling factor that reduces the error

    if result.success:
        scaling_factor = result.x[0]
        scaled_probs = base_probs * scaling_factor
        scaled_probs /= np.sum(scaled_probs) # re normalize
        return scaled_probs
    else:
        # Fallback to a basic heuristic if optimization fails
        if expected_runs <= 0:
            return np.array([1, 0, 0, 0, 0, 0])
        elif expected_runs >= 6:
            return np.array([0, 0, 0, 0, 0, 1])
        else:
            # A very simple linear approximation
            p6 = expected_runs / 6.0
            p0 = 1 - p6
            return np.array([p0, 0, 0, 0, 0, p6])

def get_ball_probabilities(expected_runs):
    """Adjust ball probabilities for ODI scoring patterns."""
    if expected_runs <= 0:
        return [1, 0, 0, 0, 0, 0, 0]  # All dots

    # ODI base probabilities - tuned for ODI style
    p0 = 0.68  # Increased dot ball probability for ODIs
    p1 = 0.25 # Increased single probability for ODIs - Strike rotation is key
    p2 = 0.04 # Slightly reduced doubles
    p3 = 0.005 # Very rare in ODIs, keep low
    p4 = 0.02  # Reduced fours, less boundary-focused than T20
    p6 = 0.005 # Significantly reduced sixes for ODI realism

    # Calculate current expected value
    current_exp = 0*p0 + 1*p1 + 2*p2 + 3*p3 + 4*p4 + 6*p6

    # Adjust probabilities to match expected runs
    scale = expected_runs / current_exp if current_exp > 0 else 0

    # Scale all non-zero probabilities
    p1 *= scale
    p2 *= scale
    p3 *= scale
    p4 *= scale
    p6 *= scale

    # Put remaining probability into dots
    p0 = 1 - (p1 + p2 + p3 + p4 + p6)

    return [p0, p1, p2, p3, p4, 0, p6]

def simulate_ball_test(striker, bowler, pitch, settled_meter, over, aggression):
    """
    Simulate a single ball in an ODI match.

    Parameters:
    - striker (Player): The batter facing the ball.
    - bowler (Player): The player bowling the ball.
    - pitch (Stadium): The pitch conditions.
    - settled_meter (float): How settled the batter is (currently unused).
    - over (int): Current over number (currently unused).

    Returns:
    - runs (int): Number of runs scored on this ball (0, 1, 2, 4, or 6).
    - out (bool): Whether the batter is out on this ball.
    - comments (list): a list of strings containing relevant lines of commentary
    - pace (float): speed of the ball
    """
    # Calculate base runs and out probabilities from striker's ODI stats
    base_runs = striker.test_sr / 100  # Expected runs per ball
    base_out = base_runs / striker.test_ave # Base probability of getting out
    turn, swing, seam, bounce, slower = 0, 0, 0, 0, False
    comments = []

    # Calculate ball attributes based on bowler type and pitch conditions
    if bowler.bowling_type == "Pace":
        # Pace bowler: calculate pace, swing, bounce, and accuracy
        if random.randint(1, 100) < 95:
            # 15% chance of bowling faster
            pace = bowler.bowling_pace + random.gauss(bowler.match_fatigue/-10, 5)
            difficulty = max(0,(pace - 130))**1.15 # -5/30
            pd = difficulty
            slower = False
        else:
            # 85% chance of bowling slower with variation
            pace = bowler.bowling_pace * 0.83 + random.gauss(2, 8)
            difficulty = (bowler.bowling_pace - pace)/3
            pd = difficulty
            slower = True 
            #print("s", end = '')
        
        #print(bowler.name, pace, difficulty)
        # Swing and bounce influenced by pitch grass cover and bounce
        swing = (bowler.bowling_swing * (pitch.grass_cover))/(100+(20 * (over%80))) * random.gauss(1, 0.2)
        difficulty *= min(swing, 0.8)
        bounce = ((bowler.bowling_bounce)/10 + (pitch.bounce)) * random.gauss(1, 0.4)
        seam = (((bowler.bowling_seam) * (pitch.hardness))/40) ** random.gauss(-0.2, 0.9)
        # Accuracy based on bowler's control
        difficulty += bounce + seam
        #difficulty = max(random.gauss(difficulty,100-bowler.control),difficulty)

        # Calculate difficulty of the ball for the batter
        # Higher pace, swing, bounce, and accuracy increase difficulty
        # Batter's bonuses (batting_fast, batting_swing, batting_bounce) reduce difficulty
        #print(f"Bowler: {bowler.name} Pace:{pd} swing:{swing} Bounce:{bounce} Seam:{seam} difficulty: {difficulty}")
        batter_bonus = (striker.batting_fast * (pace-130))/25
        batter_bonus += (striker.batting_swing * swing)/10
        batter_bonus += (striker.batting_bounce * bounce)/140
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    else:
        # Spin bowler: calculate pace (slower), turn, bounce, and accuracy
        pace = bowler.bowling_pace + random.gauss(10, 5)  # Spin pace typically between 60-80 kmph
        turn = max(bowler.bowling_turn * ((pitch.turn)/5)**1.5 * random.gauss(3, 2), 0.2)/100
        difficulty = (turn**1.2)*5
        #difficulty = max(random.gauss(difficulty,100-bowler.bowling_control),difficulty)

        batter_bonus = striker.batting_spin/6
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    # batter_bonus += settled_meter/400

    #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
        bowlfmod = max(0,min(bowlfmod,2))
    else: 
        bowlfmod = (20-bowler.match_fatigue)/30 # 1 to 0
        bowlfmod = min(max(bowlfmod,0.1),1)

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/80 #0 to 2+ 
        batfmod = max(0,min(batfmod,2))
    else: 
        batfmod = (20-striker.match_fatigue)/40 # 1 to 0
        batfmod = min(max(batfmod,0.1),0)

    #print(batfmod, bowlfmod)
    fatigue_effect = ((batfmod - bowlfmod + 3)/3) #  1.4 to 0.6


    # Scale factor for difficulty (may need tuning based on testing)
    shot = batter_bonus - (difficulty)
    
    # Calculate probability of getting out
    # Higher difficulty increases the chance of getting out

    p_out = base_out * (0.8 - (shot)/30) 
    # Determine if the batter is out
    if random.random() < p_out:
        if pace > 145: 
            comments.extend(commentary["very_fast_ball"])
        if swing > 20: 
            comments.extend(commentary["swinging_ball"])
        if slower:
            comments.extend(commentary["slower_ball"])
        if seam > 10: 
            comments.extend(commentary["seaming_ball"])
        if bounce > 10: 
            comments.extend(commentary["high_bouncer"])
        if turn > 3: 
            comments.extend(commentary["spinning_ball"])
        if difficulty < 8: 
            if bowler.bowling_type == "Pacer":
                comments.extend(commentary["bad_ball_pacer"])
            else:
                comments.extend(commentary["bad_ball_spinner"])

        if len(comments) == 0: 
            comments.extend(generic_commentary["W"])

        return 0, True, comments, pace



    runs = base_runs * (1 + shot/100) + settled_meter/500


    w = get_ball_probabilities(runs)
    r =  random.choices([0,1,2,3,4,5,6], weights=w)[0]


    if r == 0: 
        if pace > 150: 
            comments.extend(dot_ball_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(dot_ball_commentary["swinging_ball"])
        if slower:
            comments.extend(dot_ball_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(dot_ball_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(dot_ball_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(dot_ball_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(dot_ball_commentary["bad_ball_pacer"])
            else:
                comments.extend(dot_ball_commentary["bad_ball_spinner"])

    
    if r == 1: 
        if pace > 147: 
            comments.extend(single_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(single_commentary["swinging_ball"])
        if slower:
            comments.extend(single_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(single_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(single_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(single_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(single_commentary["bad_ball_pacer"])
            else:
                comments.extend(single_commentary["bad_ball_spinner"])

    if r == 2: 
        if pace > 147: 
            comments.extend(two_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(two_commentary["swinging_ball"])
        if slower:
            comments.extend(two_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(two_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(two_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(two_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(two_commentary["bad_ball_pacer"])
            else:
                comments.extend(two_commentary["bad_ball_spinner"])

    if r == 3:
        if pace > 147: 
            comments.extend(three_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(three_commentary["swinging_ball"])
        if slower:
            comments.extend(three_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(three_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(three_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(three_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(three_commentary["bad_ball_pacer"])
            else:
                comments.extend(three_commentary["bad_ball_spinner"])

    if r == 4: 
        if pace > 147: 
            comments.extend(four_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(four_commentary["swinging_ball"])
        if slower:
            comments.extend(four_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(four_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(four_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(four_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(four_commentary["bad_ball_pacer"])
            else:
                comments.extend(four_commentary["bad_ball_spinner"])

    if r == 6:
        if pace > 147: 
            comments.extend(six_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(six_commentary["swinging_ball"])
        if slower:
            comments.extend(six_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(six_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(six_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(six_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(six_commentary["bad_ball_pacer"])
            else:
                comments.extend(six_commentary["bad_ball_spinner"])

    if len(comments) == 0: 
        if r == 0:
            comments.extend(generic_commentary["."])
        elif r == 1: 
            comments.extend(generic_commentary["1"])
        elif r == 2: 
            comments.extend(generic_commentary["2"])
        elif r == 3: 
            comments.extend(generic_commentary["3"])
        elif r == 4: 
            comments.extend(generic_commentary["4"])
        elif r == 6: 
            comments.extend(generic_commentary["6"])
    return r, False, comments, pace


def simulate_ball_odi(striker, bowler, pitch, settled_meter, over, aggression):
    """
    Simulate a single ball in an ODI match.

    Parameters:
    - striker (Player): The batter facing the ball.
    - bowler (Player): The player bowling the ball.
    - pitch (Stadium): The pitch conditions.
    - settled_meter (float): How settled the batter is (currently unused).
    - over (int): Current over number (currently unused).

    Returns:
    - runs (int): Number of runs scored on this ball (0, 1, 2, 4, or 6).
    - out (bool): Whether the batter is out on this ball.
    - comments (list): a list of strings containing relevant lines of commentary
    - pace (float): speed of the ball
    """
    # Calculate base runs and out probabilities from striker's ODI stats
    base_runs = striker.odi_sr / 100  # Expected runs per ball
    base_out = base_runs * 40 / striker.odi_ave ** 2 # Base probability of getting out
    turn, swing, seam, bounce, slower = 0, 0, 0, 0, False
    comments = []

    # Calculate ball attributes based on bowler type and pitch conditions
    if bowler.bowling_type == "Pace":
        # Pace bowler: calculate pace, swing, bounce, and accuracy
        if random.randint(1, 100) < 87:
            # 15% chance of bowling faster
            pace = bowler.bowling_pace + random.gauss(0, 5)
            difficulty = max(0,(pace - 132))**1.15 # -5/30
            pd = difficulty
            slower = False
        else:
            # 85% chance of bowling slower with variation
            pace = bowler.bowling_pace * 0.83 + random.gauss(2, 8)
            difficulty = (bowler.bowling_pace - pace)/3
            pd = difficulty
            slower = True 
            #print("s", end = '')
        
        #print(bowler.name, pace, difficulty)
        # Swing and bounce influenced by pitch grass cover and bounce
        swing = (bowler.bowling_swing * (pitch.grass_cover))/(100+(100 * over)) * random.gauss(1, 0.2)
        difficulty *= min(swing, 0.8)
        bounce = ((bowler.bowling_bounce)/10 + (pitch.bounce)) * random.gauss(1, 0.4)
        seam = (((bowler.bowling_seam) * (pitch.hardness))/40) ** random.gauss(-0.2, 0.9)
        # Accuracy based on bowler's control
        difficulty += bounce + seam
        #difficulty = max(random.gauss(difficulty,100-bowler.control),difficulty)

        # Calculate difficulty of the ball for the batter
        # Higher pace, swing, bounce, and accuracy increase difficulty
        # Batter's bonuses (batting_fast, batting_swing, batting_bounce) reduce difficulty
        #print(f"Bowler: {bowler.name} Pace:{pd} swing:{swing} Bounce:{bounce} Seam:{seam} difficulty: {difficulty}")
        batter_bonus = (striker.batting_fast * (pace-130))/25
        batter_bonus += (striker.batting_swing * swing)/10
        batter_bonus += (striker.batting_bounce * bounce)/140
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    else:
        # Spin bowler: calculate pace (slower), turn, bounce, and accuracy
        pace = bowler.bowling_pace + random.gauss(10, 5)  # Spin pace typically between 60-80 kmph
        turn = max(bowler.bowling_turn * ((pitch.turn)/5)**1.5 * random.gauss(3, 2), 0.2)/100
        difficulty = (turn**1.2)*5
        #difficulty = max(random.gauss(difficulty,100-bowler.bowling_control),difficulty)

        batter_bonus = striker.batting_spin/6
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    batter_bonus += settled_meter/200

    #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
    else: 
        bowlfmod = (20-bowler.match_fatigue)/20 # 1 to 0

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/40 #0 to 2+ 
    else: 
        batfmod = (20-striker.match_fatigue)/20 # 1 to 0


    fatigue_effect = ((batfmod - bowlfmod + 3)/3)**0.3 #  1.4 to 0.6


    # Scale factor for difficulty (may need tuning based on testing)
    shot = batter_bonus - (difficulty)
    
    # Calculate probability of getting out
    # Higher difficulty increases the chance of getting out
    p_out = base_out * (0.75 - (shot)/30)/fatigue_effect * aggression
    # Determine if the batter is out
    if random.random() < p_out:
        if pace > 145: 
            comments.extend(commentary["very_fast_ball"])
        if swing > 20: 
            comments.extend(commentary["swinging_ball"])
        if slower:
            comments.extend(commentary["slower_ball"])
        if seam > 10: 
            comments.extend(commentary["seaming_ball"])
        if bounce > 10: 
            comments.extend(commentary["high_bouncer"])
        if turn > 3: 
            comments.extend(commentary["spinning_ball"])
        if difficulty < 8: 
            if bowler.bowling_type == "Pacer":
                comments.extend(commentary["bad_ball_pacer"])
            else:
                comments.extend(commentary["bad_ball_spinner"])

        if len(comments) == 0: 
            comments.extend(generic_commentary["W"])

        return 0, True, comments, pace

    runs = base_runs * (0.8 + shot/80)*fatigue_effect * aggression ** 1.5
    w = get_ball_probabilities(runs)
    r =  random.choices([0,1,2,3,4,5,6], weights=w)[0]

    if r == 0: 
        if random.randint(1,100) > (striker.batting_rotation - 50):
            r = 1
    if r == 1:
        if random.randint(1,100) < (striker.batting_rotation - 50):
            r = 0

    if r == 0: 
        if pace > 150: 
            comments.extend(dot_ball_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(dot_ball_commentary["swinging_ball"])
        if slower:
            comments.extend(dot_ball_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(dot_ball_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(dot_ball_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(dot_ball_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(dot_ball_commentary["bad_ball_pacer"])
            else:
                comments.extend(dot_ball_commentary["bad_ball_spinner"])

    
    if r == 1: 
        if pace > 147: 
            comments.extend(single_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(single_commentary["swinging_ball"])
        if slower:
            comments.extend(single_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(single_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(single_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(single_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(single_commentary["bad_ball_pacer"])
            else:
                comments.extend(single_commentary["bad_ball_spinner"])

    if r == 2: 
        if pace > 147: 
            comments.extend(two_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(two_commentary["swinging_ball"])
        if slower:
            comments.extend(two_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(two_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(two_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(two_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(two_commentary["bad_ball_pacer"])
            else:
                comments.extend(two_commentary["bad_ball_spinner"])

    if r == 3:
        if pace > 147: 
            comments.extend(three_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(three_commentary["swinging_ball"])
        if slower:
            comments.extend(three_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(three_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(three_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(three_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(three_commentary["bad_ball_pacer"])
            else:
                comments.extend(three_commentary["bad_ball_spinner"])

    if r == 4: 
        if pace > 147: 
            comments.extend(four_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(four_commentary["swinging_ball"])
        if slower:
            comments.extend(four_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(four_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(four_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(four_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(four_commentary["bad_ball_pacer"])
            else:
                comments.extend(four_commentary["bad_ball_spinner"])

    if r == 6:
        if pace > 147: 
            comments.extend(six_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(six_commentary["swinging_ball"])
        if slower:
            comments.extend(six_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(six_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(six_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(six_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(six_commentary["bad_ball_pacer"])
            else:
                comments.extend(six_commentary["bad_ball_spinner"])

    if len(comments) == 0: 
        if r == 0:
            comments.extend(generic_commentary["."])
        elif r == 1: 
            comments.extend(generic_commentary["1"])
        elif r == 2: 
            comments.extend(generic_commentary["2"])
        elif r == 3: 
            comments.extend(generic_commentary["3"])
        elif r == 4: 
            comments.extend(generic_commentary["4"])
        elif r == 6: 
            comments.extend(generic_commentary["6"])
    return r, False, comments, pace


def simulate_ball_t20(striker, bowler, pitch, settled_meter, over, aggression):
    """
    Simulate a single ball in an ODI match.

    Parameters:
    - striker (Player): The batter facing the ball.
    - bowler (Player): The player bowling the ball.
    - pitch (Stadium): The pitch conditions.
    - settled_meter (float): How settled the batter is (currently unused).
    - over (int): Current over number (currently unused).

    Returns:
    - runs (int): Number of runs scored on this ball (0, 1, 2, 4, or 6).
    - out (bool): Whether the batter is out on this ball.
    - comments (list): a list of strings containing relevant lines of commentary
    - pace (float): speed of the ball
    """
    # Calculate base runs and out probabilities from striker's ODI stats
    base_runs = (striker.t20_sr+20)/ 100  # Expected runs per ball
    base_out = base_runs / striker.t20_ave # Base probability of getting out
    turn, swing, seam, bounce, slower = 0, 0, 0, 0, False
    comments = []

    # Calculate ball attributes based on bowler type and pitch conditions
    if bowler.bowling_type == "Pace":
        # Pace bowler: calculate pace, swing, bounce, and accuracy
        if random.randint(1, 100) < 87:
            # 15% chance of bowling faster
            pace = bowler.bowling_pace + random.gauss(0, 5)
            difficulty = max(0,(pace - 132))**1.15 # -5/30
            pd = difficulty
            slower = False
        else:
            # 85% chance of bowling slower with variation
            pace = bowler.bowling_pace * 0.83 + random.gauss(2, 8)
            difficulty = (bowler.bowling_pace - pace)/3
            pd = difficulty
            slower = True 
            #print("s", end = '')
        
        #print(bowler.name, pace, difficulty)
        # Swing and bounce influenced by pitch grass cover and bounce
        swing = (bowler.bowling_swing * (pitch.grass_cover))/(100+(100 * over)) * random.gauss(1, 0.2)
        difficulty *= min(swing, 0.8)
        bounce = ((bowler.bowling_bounce)/10 + (pitch.bounce)) * random.gauss(1, 0.4)
        seam = (((bowler.bowling_seam) * (pitch.hardness))/40) ** random.gauss(-0.2, 0.9)
        # Accuracy based on bowler's control
        difficulty += bounce + seam
        #difficulty = max(random.gauss(difficulty,100-bowler.control),difficulty)

        # Calculate difficulty of the ball for the batter
        # Higher pace, swing, bounce, and accuracy increase difficulty
        # Batter's bonuses (batting_fast, batting_swing, batting_bounce) reduce difficulty
        #print(f"Bowler: {bowler.name} Pace:{pd} swing:{swing} Bounce:{bounce} Seam:{seam} difficulty: {difficulty}")
        batter_bonus = (striker.batting_fast * (pace-130))/25
        batter_bonus += (striker.batting_swing * swing)/10
        batter_bonus += (striker.batting_bounce * bounce)/140
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    else:
        # Spin bowler: calculate pace (slower), turn, bounce, and accuracy
        pace = bowler.bowling_pace + random.gauss(10, 5)  # Spin pace typically between 60-80 kmph
        turn = max(bowler.bowling_turn * ((pitch.turn)/5)**1.5 * random.gauss(3, 2), 0.2)/100
        difficulty = (turn**1.1)*4
        #difficulty = max(random.gauss(difficulty,100-bowler.bowling_control),difficulty)

        batter_bonus = striker.batting_spin/6
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    batter_bonus += settled_meter/200

    #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
        bowlfmod = max(0,min(bowlfmod,2))
    else: 
        bowlfmod = (20-bowler.match_fatigue)/30 # 1 to 0
        bowlfmod = min(max(bowlfmod,0.1),1)

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/80 #0 to 2+ 
        batfmod = max(0,min(batfmod,2))
    else: 
        batfmod = (20-striker.match_fatigue)/40 # 1 to 0
        batfmod = min(max(batfmod,0.1),0)



    fatigue_effect = ((batfmod - bowlfmod + 3)/3)**0.2 #  1.4 to 0.6


    # Scale factor for difficulty (may need tuning based on testing)
    shot = batter_bonus - (difficulty)
    
    # Calculate probability of getting out
    # Higher difficulty increases the chance of getting out
    p_out = base_out * (1 - (shot)/30)/fatigue_effect * aggression 
    # Determine if the batter is out
    if random.random() < p_out:
        if pace > 145: 
            comments.extend(commentary["very_fast_ball"])
        if swing > 20: 
            comments.extend(commentary["swinging_ball"])
        if slower:
            comments.extend(commentary["slower_ball"])
        if seam > 10: 
            comments.extend(commentary["seaming_ball"])
        if bounce > 10: 
            comments.extend(commentary["high_bouncer"])
        if turn > 3: 
            comments.extend(commentary["spinning_ball"])
        if difficulty < 8: 
            if bowler.bowling_type == "Pacer":
                comments.extend(commentary["bad_ball_pacer"])
            else:
                comments.extend(commentary["bad_ball_spinner"])

        if len(comments) == 0: 
            comments.extend(generic_commentary["W"])

        return 0, True, comments, pace

    runs = random.gauss(base_runs * (1.4 + shot/40)*fatigue_effect * aggression, 0.3) + settled_meter/50
    w = get_ball_probabilities(runs)
    r =  random.choices([0,1,2,3,4,5,6], weights=w)[0]

    if r == 0: 
        if random.randint(1,100) > (striker.batting_rotation - 50):
            r = 1
    if r == 1:
        if random.randint(1,100) < (striker.batting_rotation - 50):
            r = 0

    if r == 0: 
        if pace > 150: 
            comments.extend(dot_ball_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(dot_ball_commentary["swinging_ball"])
        if slower:
            comments.extend(dot_ball_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(dot_ball_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(dot_ball_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(dot_ball_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(dot_ball_commentary["bad_ball_pacer"])
            else:
                comments.extend(dot_ball_commentary["bad_ball_spinner"])

    
    if r == 1: 
        if pace > 147: 
            comments.extend(single_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(single_commentary["swinging_ball"])
        if slower:
            comments.extend(single_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(single_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(single_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(single_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(single_commentary["bad_ball_pacer"])
            else:
                comments.extend(single_commentary["bad_ball_spinner"])

    if r == 2: 
        if pace > 147: 
            comments.extend(two_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(two_commentary["swinging_ball"])
        if slower:
            comments.extend(two_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(two_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(two_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(two_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(two_commentary["bad_ball_pacer"])
            else:
                comments.extend(two_commentary["bad_ball_spinner"])

    if r == 3:
        if pace > 147: 
            comments.extend(three_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(three_commentary["swinging_ball"])
        if slower:
            comments.extend(three_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(three_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(three_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(three_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(three_commentary["bad_ball_pacer"])
            else:
                comments.extend(three_commentary["bad_ball_spinner"])

    if r == 4: 
        if pace > 147: 
            comments.extend(four_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(four_commentary["swinging_ball"])
        if slower:
            comments.extend(four_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(four_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(four_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(four_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(four_commentary["bad_ball_pacer"])
            else:
                comments.extend(four_commentary["bad_ball_spinner"])

    if r == 6:
        if pace > 147: 
            comments.extend(six_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(six_commentary["swinging_ball"])
        if slower:
            comments.extend(six_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(six_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(six_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(six_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(six_commentary["bad_ball_pacer"])
            else:
                comments.extend(six_commentary["bad_ball_spinner"])

    if len(comments) == 0: 
        if r == 0:
            comments.extend(generic_commentary["."])
        elif r == 1: 
            comments.extend(generic_commentary["1"])
        elif r == 2: 
            comments.extend(generic_commentary["2"])
        elif r == 3: 
            comments.extend(generic_commentary["3"])
        elif r == 4: 
            comments.extend(generic_commentary["4"])
        elif r == 6: 
            comments.extend(generic_commentary["6"])
    return r, False, comments, pace


def simulate_odi(team1, team2, venue):
    """Simulate a match between any two teams."""
    # Random toss to decide who bats first
    if random.randint(1, 100) > 100:
        team1, team2 = team2, team1
    
    pitch = venue
    
    # Simulate first innings
    team1_score, team1_wickets, team1_batting_stats, team1_bowling_stats = simulate_odi_innings(team1, team2, pitch)
    
    # Display scorecard for team 1
    display_scorecard(team1_batting_stats, team1_bowling_stats, team1.name, team1_score, team1_wickets, [])
    
    # Simulate second innings
    team2_score, team2_wickets, team2_batting_stats, team2_bowling_stats = simulate_odi_innings(team2, team1, pitch, team1_score)

    
    # Display scorecard for team 2
    display_scorecard(team2_batting_stats, team2_bowling_stats, team2.name, team2_score, team2_wickets, [])

    # Determine winner
    if team1_score > team2_score:
        print(f"\n{team1.name} wins by {team1_score - team2_score} runs!")
    elif team2_score > team1_score:
        print(f"\n{team2.name} wins by {10 - team2_wickets} wickets!")
    else:
        print("\nMatch tied!")
    
    return (team1_score, team1_wickets, team2_score, team2_wickets)


def simulate_t20(team1, team2, venue):
    """Simulate a match between any two teams."""
    # Random toss to decide who bats first
    if random.randint(1, 100) > 100:
        team1, team2 = team2, team1
    
    pitch = venue
    
    # Simulate first innings
    team1_score, team1_wickets, team1_batting_stats, team1_bowling_stats = simulate_t20_innings(team1, team2, pitch)
    
    # Display scorecard for team 1
    display_scorecard(team1_batting_stats, team1_bowling_stats, team1.name, team1_score, team1_wickets, [])
    
    # Simulate second innings
    team2_score, team2_wickets, team2_batting_stats, team2_bowling_stats = simulate_t20_innings(team2, team1, pitch, team1_score)

    
    # Display scorecard for team 2
    display_scorecard(team2_batting_stats, team2_bowling_stats, team2.name, team2_score, team2_wickets, [])

    # Determine winner
    if team1_score > team2_score:
        print(f"\n{team1.name} wins by {team1_score - team2_score} runs!")
    elif team2_score > team1_score:
        print(f"\n{team2.name} wins by {10 - team2_wickets} wickets!")
    else:
        print("\nMatch tied!")
    
    return (team1_score, team1_wickets, team2_score, team2_wickets)


def select_bowler_test(bowling_team, bowled_overs, over_number, previous_bowler, bowling_stats):
    """
    Select the best bowler for the current over in an ODI match.

    Parameters:
    - bowling_team (Team): The team bowling, with Player objects in team.players.
    - bowled_overs (dict): Dictionary mapping bowler names to the number of overs they’ve bowled.
    - over_number (int): The current over number (0 to 49).
    - previous_bowler (Player or None): The bowler who bowled the previous over (None for first over).
    - bowling_stats (dict): Dictionary of bowler performance stats {name: {"overs": int, "m": int, "runs": int, "wickets": int}}.

    Returns:
    - Player: The selected bowler as a Player object.
    """
    # Step 1: Filter available bowlers based on constraints
    available_bowlers = []
    for player in bowling_team.players:
        name = player.name
        overs_bowled = bowled_overs.get(name, 0)
        
        # Exclude if bowled 10 overs or was the previous bowler
        if (previous_bowler is None or name != previous_bowler.name):
            available_bowlers.append(player)
    
    if not available_bowlers:
        raise ValueError("No available bowlers meet the criteria!")

    # Step 2: Define situational weights based on over number
    if over_number % 80 < 30:  # Powerplay (overs 0-9)
        # Favor pace bowlers with swing/control for early wickets
        situation_weights = {
            "pace": 1.5,         # Boost for pace bowlers
            "swing": 1.8,        # Swing to exploit new ball
            "control": 1.3,      # Accuracy for tight lines
            "wickets": 0.5,      # Prioritize wicket-taking
            "economy": 0.6,  
            "spin": -0.5     # Less focus on economy early
        }
    else:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.0,
            "swing": 0.8,
            "control": 1.2,
            "wickets": 0.5,
            "economy": 1,
            "spin": 1.5        # Control runs in middle phase
        }


    bowler_scores = []
    for bowler in available_bowlers:
        name = bowler.name
        stats = bowling_stats.get(name, {"overs": 0, "runs": 0, "wickets": 0})
        
        # Base ability scores from Player attributes
        pace_score = bowler.bowling_pace / 100
        swing = bowler.bowling_swing / 100 if hasattr(bowler, 'bowling_swing') else bowler.bowling_turn / 100  # Use turn for spinners
        control_score = bowler.bowling_control / 100
        spin_score = bowler.bowling_turn / 100 
        if bowler.bowling_type =="Finger":
            spin_score = spin_score + 0.3
        
        # Performance scores from current match
        overs_bowled = stats["overs"]
        wickets = stats["wickets"]
        runs = stats["runs"]
        economy = (max(0,(runs - overs_bowled * 1)))/(overs_bowled+1)** 0.5
        
        # Normalize performance: reward wickets, penalize high economy
        wicket_score = min(wickets / 5, 1.0)  # Cap at 5 wickets for max score
        economy_score = max(0, 1 - (economy - 6) / 6)  # Ideal economy ~6, penalize above
        
        # Combine scores with situational weights
        total_score = (
            situation_weights["pace"] * pace_score +
            situation_weights["swing"] * swing +
            situation_weights["control"] * control_score +
            situation_weights["wickets"] * wicket_score +
            situation_weights["economy"] * economy_score +
            situation_weights["spin"] * spin_score
        )
        
        # Adjust for freshness: slightly favor bowlers who’ve bowled less
        total_score = total_score - (bowler.match_fatigue*total_score/200)
        
        bowler_scores.append((bowler, total_score))
        if bowler.match_fatigue > 20:
            bowler.match_fatigue -= 4

    # Step 4: Select top candidates and add randomness for variety
    if not bowler_scores:
        raise ValueError("No bowlers could be scored!")
    
    # Sort by score descending
    bowler_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick from top 3 (or fewer) to avoid always choosing the same bowler
    top_n = min(3, len(bowler_scores))
    top_bowlers = bowler_scores[:top_n]
    selected_bowler = random.choices(
        [b[0] for b in top_bowlers], 
        weights=[max(0.01,b[1]) for b in top_bowlers], 
        k=1
    )[0]

    # Debug output (optional)
    # print(f"Over {over_number + 1}: Selected {selected_bowler.name} (Score: {dict(bowler_scores)[selected_bowler]:.2f})")
    selected_bowler.match_fatigue += 100/selected_bowler.fitness
    return selected_bowler


def select_bowler_odi(bowling_team, bowled_overs, over_number, previous_bowler, bowling_stats):
    """
    Select the best bowler for the current over in an ODI match.

    Parameters:
    - bowling_team (Team): The team bowling, with Player objects in team.players.
    - bowled_overs (dict): Dictionary mapping bowler names to the number of overs they’ve bowled.
    - over_number (int): The current over number (0 to 49).
    - previous_bowler (Player or None): The bowler who bowled the previous over (None for first over).
    - bowling_stats (dict): Dictionary of bowler performance stats {name: {"overs": int, "m": int, "runs": int, "wickets": int}}.

    Returns:
    - Player: The selected bowler as a Player object.
    """
    # Step 1: Filter available bowlers based on constraints
    available_bowlers = []
    for player in bowling_team.players:
        name = player.name
        overs_bowled = bowled_overs.get(name, 0)
        
        # Exclude if bowled 10 overs or was the previous bowler
        if (previous_bowler is None or name != previous_bowler.name) and (overs_bowled < 10):
            available_bowlers.append(player)
    
    if not available_bowlers:
        raise ValueError("No available bowlers meet the criteria!")

    # Step 2: Define situational weights based on over number
    if over_number < 10:  # Powerplay (overs 0-9)
        # Favor pace bowlers with swing/control for early wickets
        situation_weights = {
            "pace": 1.5,         # Boost for pace bowlers
            "swing": 1.8,        # Swing to exploit new ball
            "control": 1.3,      # Accuracy for tight lines
            "wickets": 1.2,      # Prioritize wicket-taking
            "economy": 0.6,  
            "spin": -0.3     # Less focus on economy early
        }
    elif over_number < 40:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.0,
            "swing": 0.8,
            "control": 1.2,
            "wickets": 0.5,
            "economy": 1,
            "spin": 1.5        # Control runs in middle phase
        }

    else:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.3,
            "swing": 0.4,
            "control": 1.5,
            "wickets": 0.5,
            "economy": 1.3,
            "spin": 0.3       # Control runs in middle phase
        }
    bowler_scores = []
    for bowler in available_bowlers:
        name = bowler.name
        stats = bowling_stats.get(name, {"overs": 0, "runs": 0, "wickets": 0})
        
        # Base ability scores from Player attributes
        pace_score = bowler.bowling_pace / 100
        swing = bowler.bowling_swing / 100 if hasattr(bowler, 'bowling_swing') else bowler.bowling_turn / 100  # Use turn for spinners
        control_score = bowler.bowling_control / 100
        spin_score = bowler.bowling_turn / 100 
        if bowler.bowling_type =="Finger":
            spin_score = spin_score + 0.3
        
        # Performance scores from current match
        overs_bowled = stats["overs"]
        wickets = stats["wickets"]
        runs = stats["runs"]
        economy = max(0,(runs - overs_bowled * 7))** 0.5
        
        # Normalize performance: reward wickets, penalize high economy
        wicket_score = min(wickets / 5, 1.0)  # Cap at 5 wickets for max score
        economy_score = max(0, 1 - (economy - 6) / 6)  # Ideal economy ~6, penalize above
        
        # Combine scores with situational weights
        total_score = (
            situation_weights["pace"] * pace_score +
            situation_weights["swing"] * swing +
            situation_weights["control"] * control_score +
            situation_weights["wickets"] * wicket_score +
            situation_weights["economy"] * economy_score +
            situation_weights["spin"] * spin_score
        )
        
        # Adjust for freshness: slightly favor bowlers who’ve bowled less
        total_score = total_score - (bowler.match_fatigue*total_score/200)
        
        bowler_scores.append((bowler, total_score))
        if bowler.match_fatigue > 20:
            bowler.match_fatigue -= 2

    # Step 4: Select top candidates and add randomness for variety
    if not bowler_scores:
        raise ValueError("No bowlers could be scored!")
    
    # Sort by score descending
    bowler_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick from top 3 (or fewer) to avoid always choosing the same bowler
    top_n = min(3, len(bowler_scores))
    top_bowlers = bowler_scores[:top_n]
    selected_bowler = random.choices(
        [b[0] for b in top_bowlers], 
        weights=[b[1] for b in top_bowlers], 
        k=1
    )[0]

    # Debug output (optional)
    # print(f"Over {over_number + 1}: Selected {selected_bowler.name} (Score: {dict(bowler_scores)[selected_bowler]:.2f})")
    selected_bowler.match_fatigue += 100/selected_bowler.fitness
    return selected_bowler



def select_bowler_t20(bowling_team, bowled_overs, over_number, previous_bowler, bowling_stats):
    """
    Select the best bowler for the current over in an ODI match.

    Parameters:
    - bowling_team (Team): The team bowling, with Player objects in team.players.
    - bowled_overs (dict): Dictionary mapping bowler names to the number of overs they’ve bowled.
    - over_number (int): The current over number (0 to 49).
    - previous_bowler (Player or None): The bowler who bowled the previous over (None for first over).
    - bowling_stats (dict): Dictionary of bowler performance stats {name: {"overs": int, "m": int, "runs": int, "wickets": int}}.

    Returns:
    - Player: The selected bowler as a Player object.
    """
    # Step 1: Filter available bowlers based on constraints
    available_bowlers = []
    for player in bowling_team.players:
        name = player.name
        overs_bowled = bowled_overs.get(name, 0)
        
        # Exclude if bowled 10 overs or was the previous bowler
        if (previous_bowler is None or name != previous_bowler.name) and (overs_bowled < 4):
            available_bowlers.append(player)
    
    if not available_bowlers:
        raise ValueError("No available bowlers meet the criteria!")

    # Step 2: Define situational weights based on over number
    if over_number < 6:  # Powerplay (overs 0-9)
        # Favor pace bowlers with swing/control for early wickets
        situation_weights = {
            "pace": 1.5,         # Boost for pace bowlers
            "swing": 1.8,        # Swing to exploit new ball
            "control": 1.3,      # Accuracy for tight lines
            "wickets": 1.2,      # Prioritize wicket-taking
            "economy": 0.6,  
            "spin": -0.5     # Less focus on economy early
        }
    elif over_number < 15:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.0,
            "swing": 0.8,
            "control": 1.2,
            "wickets": 0.5,
            "economy": 1,
            "spin": 1.5        # Control runs in middle phase
        }

    else:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.3,
            "swing": 0.4,
            "control": 1.5,
            "wickets": 0.5,
            "economy": 1.3,
            "spin": 0.6        # Control runs in middle phase
        }
    bowler_scores = []
    for bowler in available_bowlers:
        name = bowler.name
        stats = bowling_stats.get(name, {"overs": 0, "runs": 0, "wickets": 0})
        
        # Base ability scores from Player attributes
        pace_score = bowler.bowling_pace / 100
        swing = bowler.bowling_swing / 100 if hasattr(bowler, 'bowling_swing') else bowler.bowling_turn / 100  # Use turn for spinners
        control_score = bowler.bowling_control / 100
        spin_score = bowler.bowling_turn / 100 
        if bowler.bowling_type =="Finger":
            spin_score = spin_score + 0.3
        
        # Performance scores from current match
        overs_bowled = stats["overs"]
        wickets = stats["wickets"]
        runs = stats["runs"]
        economy = max(0,(runs - overs_bowled * 7))** 0.5
        
        # Normalize performance: reward wickets, penalize high economy
        wicket_score = min(wickets / 5, 1.0)  # Cap at 5 wickets for max score
        economy_score = max(0, 1 - (economy - 6) / 6)  # Ideal economy ~6, penalize above
        
        # Combine scores with situational weights
        total_score = (
            situation_weights["pace"] * pace_score +
            situation_weights["swing"] * swing +
            situation_weights["control"] * control_score +
            situation_weights["wickets"] * wicket_score +
            situation_weights["economy"] * economy_score +
            situation_weights["spin"] * spin_score
        )
        
        # Adjust for freshness: slightly favor bowlers who’ve bowled less
        total_score = total_score - (bowler.match_fatigue*total_score/200)
        
        bowler_scores.append((bowler, total_score))
        if bowler.match_fatigue > 20:
            bowler.match_fatigue -= 2

    # Step 4: Select top candidates and add randomness for variety
    if not bowler_scores:
        raise ValueError("No bowlers could be scored!")
    
    # Sort by score descending
    bowler_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick from top 3 (or fewer) to avoid always choosing the same bowler
    top_n = min(3, len(bowler_scores))
    top_bowlers = bowler_scores[:top_n]
    selected_bowler = random.choices(
        [b[0] for b in top_bowlers], 
        weights=[b[1] for b in top_bowlers], 
        k=1
    )[0]

    # Debug output (optional)
    # print(f"Over {over_number + 1}: Selected {selected_bowler.name} (Score: {dict(bowler_scores)[selected_bowler]:.2f})")
    selected_bowler.match_fatigue += 100/selected_bowler.fitness
    return selected_bowler




def simulate_t20_innings(batting_team: Team, bowling_team: Team, venue, target=None):
    score = 0
    wickets = 0
    bowled_overs = {}
    batsman_index = 2
    gamewon = False
    bowler = None
    
    batting_stats = {player.name: {"runs": 0, "balls": 0, "out": False} for player in batting_team.players}
    bowling_stats = {player.name: {"overs": 0, "manameens": 0, "runs": 0, "wickets": 0} for player in bowling_team.players}
    settled_meters = {player.name: 0 for player in batting_team.players}

    striker = batting_team.players[0]
    non_striker = batting_team.players[1]
    
    for over in range(20):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_t20(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #print(f"\nOver {over + 1}: {bowler.name} bowling")
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = calculate_aggression_odi(over, venue, target, striker, non_striker, settled_meters[striker.name], settled_meters[non_striker.name])
            run, out, comments, pace = simulate_ball_t20(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            #print(f"{over}.{ball+1} {bowler.name} to {striker.name} | {run} Runs. | {pace} {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 20/bowler.fitness
            if run < 4: 
                striker.match_fatigue += run * 40/bowler.fitness
                non_striker.match_fatigue += run * 40/bowler.fitness
            
            
            if out:
                wickets += 1
                batting_stats[striker.name]["out"] = True
                bowling_stats[bowler.name]["wickets"] += 1
                if batsman_index < len(batting_team.players):
                    striker = batting_team.players[batsman_index]
                    settled_meters[striker.name] = 0
                    batsman_index += 1
            else:
                score += run
                batting_stats[striker.name]["runs"] += run
                if target and score > target:
                    gamewon = True
                if settled_meters[striker.name] < 50:
                    settled_meters[striker.name] += -0.4 + run*0.8
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: OUT! Score {score}/{wickets}\n"
            else:
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: {run} Runs. Score {score}/{wickets}\n"
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats

def simulate_odi_innings(batting_team: Team, bowling_team: Team, venue, target=None):
    score = 0
    wickets = 0
    bowled_overs = {}
    batsman_index = 2
    gamewon = False
    bowler = None
    
    batting_stats = {player.name: {"runs": 0, "balls": 0, "out": False} for player in batting_team.players}
    bowling_stats = {player.name: {"overs": 0, "manameens": 0, "runs": 0, "wickets": 0} for player in bowling_team.players}
    settled_meters = {player.name: 0 for player in batting_team.players}

    striker = batting_team.players[0]
    non_striker = batting_team.players[1]
    
    for over in range(50):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_odi(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #print(f"\nOver {over + 1}: {bowler.name} bowling")
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = calculate_aggression_odi(over, venue, target, striker, non_striker, settled_meters[striker.name], settled_meters[non_striker.name])
            run, out, comments, pace = simulate_ball_odi(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            #print(f"{over}.{ball+1} {bowler.name} to {striker.name} | {run} Runs. | {pace} {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 20/bowler.fitness
            if run < 4: 
                striker.match_fatigue += run * 40/bowler.fitness
                non_striker.match_fatigue += run * 40/bowler.fitness
            
            
            if out:
                wickets += 1
                batting_stats[striker.name]["out"] = True
                bowling_stats[bowler.name]["wickets"] += 1
                if batsman_index < len(batting_team.players):
                    striker = batting_team.players[batsman_index]
                    settled_meters[striker.name] = 0
                    batsman_index += 1
            else:
                score += run
                batting_stats[striker.name]["runs"] += run
                if target and score > target:
                    gamewon = True
                if settled_meters[striker.name] < 80:
                    settled_meters[striker.name] += run * 0.65 + 0.4
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: OUT! Score {score}/{wickets}\n"
            else:
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: {run} Runs. Score {score}/{wickets}\n"
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats
        


def simulate_test_innings(batting_team: Team, bowling_team: Team, venue, target=None):
    score = 0
    wickets = 0
    bowled_overs = {}
    batsman_index = 2
    gamewon = False
    bowler = None
    
    batting_stats = {player.name: {"runs": 0, "balls": 0, "out": False} for player in batting_team.players}
    bowling_stats = {player.name: {"overs": 0, "manameens": 0, "runs": 0, "wickets": 0} for player in bowling_team.players}
    settled_meters = {player.name: 0 for player in batting_team.players}

    striker = batting_team.players[0]
    non_striker = batting_team.players[1]
    
    for over in range(200):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_test(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #print(f"\nOver {over + 1}: {bowler.name} bowling")
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = 1
            run, out, comments, pace = simulate_ball_test(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            #print(f"{over}.{ball+1} {bowler.name} to {striker.name} | {run} Runs. | {pace} {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 10/bowler.fitness
            if run < 4: 
                striker.match_fatigue += run * 20/bowler.fitness
                non_striker.match_fatigue += run * 20/bowler.fitness
            
            
            if out:
                wickets += 1
                batting_stats[striker.name]["out"] = True
                bowling_stats[bowler.name]["wickets"] += 1
                if batsman_index < len(batting_team.players):
                    striker = batting_team.players[batsman_index]
                    settled_meters[striker.name] = 0
                    batsman_index += 1
            else:
                score += run
                batting_stats[striker.name]["runs"] += run
                if target and score > target:
                    gamewon = True
                if settled_meters[striker.name] < 80:
                    settled_meters[striker.name] += run * 0.3 + 0.2
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: OUT! Score {score}/{wickets}\n"
            else:
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: {run} Runs. Score {score}/{wickets}\n"
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats
        
def run_simulation_analysis(num_simulations=20, match_format="t20"):
    """
    Run multiple match simulations and display summary statistics to help fine-tune the simulate_ball methods.
    
    Args:
        num_simulations: Number of simulations to run
        match_format: Match format ("t20", "odi", or "test")
    """
    # Load data
    players = read_cricketers("data/players.csv")
    teams = read_teams("data/teams.csv", players)
    grounds = read_grounds("data/venues.csv")
    
    # Select two random teams and a random venue for consistent comparison
    team1, team2 = random.sample(teams, 2)
    venue = random.choice(grounds)
    
    print(f"Running {num_simulations} {match_format.upper()} match simulations between {team1.name} and {team2.name} at {venue.name}")
    
    # Initialize data collection
    match_results = []
    batting_stats = {
        "total_runs": [],
        "innings_scores": [],
        "wickets_lost": [],
        "boundaries": {"fours": 0, "sixes": 0},
        "dots": 0,
        "total_balls": 0
    }
    bowling_stats = {
        "economy_rates": [],
        "wicket_takers": {}
    }
    player_performances = {}
    
    # Initialize player performance tracking
    for player in team1.players + team2.players:
        player_performances[player.name] = {
            "innings": 0,
            "runs": [],
            "batting_avg": 0,
            "balls_faced": [],
            "strike_rate": [],
            "overs_bowled": [],
            "runs_conceded": [],
            "wickets": [],
            "economy": []
        }
    
    # Run simulations
    for i in range(num_simulations):
        print(f"Running simulation {i+1}/{num_simulations}...")
        
        # Reset match fitness for all players
        for player in team1.players + team2.players:
            player.set_match_fitness()
            
        # Run appropriate simulation
        if match_format.lower() == "t20":
            team1_score, team1_wickets, team2_score, team2_wickets = simulate_t20(team1, team2, venue)
        elif match_format.lower() == "odi":
            team1_score, team1_wickets, team2_score, team2_wickets = simulate_odi(team1, team2, venue)
        elif match_format.lower() == "test":
            # Test matches need different handling for their stats
            simulate_test(team1, team2, venue)
            continue
        
        # Record match result
        match_results.append({
            "team1_score": team1_score,
            "team1_wickets": team1_wickets,
            "team2_score": team2_score, 
            "team2_wickets": team2_wickets,
            "winner": team1.name if team1_score > team2_score else team2.name,
            "margin": f"{team1_score - team2_score} runs" if team1_score > team2_score else f"{10 - team2_wickets} wickets"
        })
        
        # Record batting stats
        batting_stats["total_runs"].append(team1_score + team2_score)
        batting_stats["innings_scores"].extend([team1_score, team2_score])
        batting_stats["wickets_lost"].extend([team1_wickets, team2_wickets])
        
        # More detailed stats would be collected from the ball-by-ball data
        # To implement this fully, you would need to modify your simulate_ball methods
        # to return more detailed statistics
    
    # Analyze and display results
    display_simulation_results(match_results, batting_stats, bowling_stats, player_performances, match_format)

def display_simulation_results(match_results, batting_stats, bowling_stats, player_performances, match_format):
    """Display summary statistics from the simulations."""
    # Calculate match statistics
    total_matches = len(match_results)
    team_wins = {}
    for result in match_results:
        winner = result["winner"]
        team_wins[winner] = team_wins.get(winner, 0) + 1
    
    # Format message
    message = f"\n==== Simulation Results Summary ({match_format.upper()}) ====\n"
    
    # Match outcomes
    message += "\nMatch Outcomes:\n"
    for team, wins in team_wins.items():
        message += f"{team}: {wins} wins ({wins/total_matches*100:.1f}%)\n"
    
    # Batting statistics
    message += "\nBatting Statistics:\n"
    message += f"Average total match runs: {sum(batting_stats['total_runs'])/len(batting_stats['total_runs']):.1f}\n"
    message += f"Average innings score: {sum(batting_stats['innings_scores'])/len(batting_stats['innings_scores']):.1f}\n"
    message += f"Average wickets per innings: {sum(batting_stats['wickets_lost'])/len(batting_stats['wickets_lost']):.1f}\n"
    
    # Distribution of innings scores
    scores = batting_stats['innings_scores']
    score_ranges = {
        "0-99": len([s for s in scores if s < 100]),
        "100-149": len([s for s in scores if 100 <= s < 150]),
        "150-199": len([s for s in scores if 150 <= s < 200]),
        "200+": len([s for s in scores if s >= 200])
    }
    
    message += "\nScore Distribution:\n"
    for range_name, count in score_ranges.items():
        message += f"{range_name}: {count} innings ({count/len(scores)*100:.1f}%)\n"
    
    # Analysis recommendations
    message += "\nRecommendations for Fine-tuning:\n"
    
    avg_score = sum(batting_stats['innings_scores'])/len(batting_stats['innings_scores'])
    if match_format == "t20" and avg_score < 140:
        message += "- T20 scores appear low. Consider increasing batting aggression or reducing bowling effectiveness.\n"
    elif match_format == "t20" and avg_score > 180:
        message += "- T20 scores appear high. Consider decreasing batting aggression or increasing bowling effectiveness.\n"
    
    if match_format == "odi" and avg_score < 240:
        message += "- ODI scores appear low. Consider increasing batting aggression or reducing bowling effectiveness.\n"
    elif match_format == "odi" and avg_score > 320:
        message += "- ODI scores appear high. Consider decreasing batting aggression or increasing bowling effectiveness.\n"
    
    avg_wickets = sum(batting_stats['wickets_lost'])/len(batting_stats['wickets_lost'])
    if avg_wickets < 6:
        message += "- Not enough wickets are falling. Consider increasing bowling effectiveness.\n"
    elif avg_wickets > 9:
        message += "- Too many wickets are falling. Consider reducing bowling effectiveness or increasing batting defense.\n"
    
    print(message)

    # Create histogram of innings scores
    if len(batting_stats['innings_scores']) > 0:
        create_score_histogram(batting_stats['innings_scores'], match_format)

def create_score_histogram(scores, match_format):
    """Create and print a histogram of innings scores."""
    # Determine bins based on match format
    if match_format == "t20":
        bins = [0, 100, 125, 150, 175, 200, 225, 250]
    elif match_format == "odi":
        bins = [0, 150, 200, 250, 300, 350, 400, 450]
    else:  # test
        bins = [0, 100, 200, 300, 400, 500, 600, 700]
    
    # Count scores in each bin
    bin_counts = [0] * (len(bins) - 1)
    for score in scores:
        for i in range(len(bins) - 1):
            if bins[i] <= score < bins[i+1]:
                bin_counts[i] += 1
                break
    
    # Create ASCII histogram
    max_count = max(bin_counts) if bin_counts else 0
    scale = 40 / max_count if max_count > 0 else 1
    
    print(f"\nInnings Score Distribution ({match_format.upper()}):")
    for i in range(len(bins) - 1):
        label = f"{bins[i]}-{bins[i+1]-1}"
        bar = "#" * int(bin_counts[i] * scale)
        print(f"{label:10} | {bar} {bin_counts[i]}")


def collect_ball_data(match_format="t20", num_balls=1000):
    """
    Collect and analyze individual ball data to fine-tune the simulate_ball methods.
    
    Args:
        match_format: The match format to analyze ("t20", "odi", "test")
        num_balls: Number of ball simulations to run
    """
    players = read_cricketers("data/players.csv")
    teams = read_teams("data/teams.csv", players)
    grounds = read_grounds("data/venues.csv")
    
    # Select random players and venue
    batting_team = random.choice(teams)
    bowling_team = random.choice([t for t in teams if t != batting_team])
    venue = random.choice(grounds)
    
    batsmen = batting_team.players[:6]  # Top 6 batsmen
    bowlers = bowling_team.players[-4:]  # Decent bowlers
    
    # Validate we have enough players
    if not bowlers:
        bowlers = bowling_team.players[:3]  # Just take first 3 if no good bowlers
    
    print(f"Analyzing {num_balls} balls for {match_format} format")
    
    # Result tracking
    results = {
        "runs": [],
        "wickets": 0,
        "dot_balls": 0,
        "boundaries": {"fours": 0, "sixes": 0},
        "run_distribution": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 6: 0},
        "pace_distribution": [],
        "runs_by_aggression": {},
        "wickets_by_aggression": {},
        "runs_by_settle": {},
        "wickets_by_settle": {}
    }
    
    # Run ball simulations
    for i in range(num_balls):
        # Select random batsman and bowler
        batsman = random.choice(batsmen)
        bowler = random.choice(bowlers)
        
        # Randomize game situation
        over = random.randint(0, 19 if match_format == "t20" else 49)
        settle_meter = random.uniform(0, 100)
        aggression = random.uniform(0.5, 2.0)
        
        # Simulate the ball based on format
        if match_format == "t20":
            run, out, _, pace = simulate_ball_t20(batsman, bowler, venue, settle_meter, over, aggression)
        elif match_format == "odi":
            run, out, _, pace = simulate_ball_odi(batsman, bowler, venue, settle_meter, over, aggression)
        else:  # test
            run, out, _, pace = simulate_ball_test(batsman, bowler, venue, settle_meter, over, aggression)
        
        # Record results
        results["runs"].append(run)
        results["pace_distribution"].append(pace)
        
        # Track run distribution
        results["run_distribution"][run if run in [0, 1, 2, 3, 4, 6] else 0] += 1
        
        if out:
            results["wickets"] += 1
        if run == 0 and not out:
            results["dot_balls"] += 1
        if run == 4:
            results["boundaries"]["fours"] += 1
        if run == 6:
            results["boundaries"]["sixes"] += 1
        
        # Track by aggression (rounded to nearest 0.1)
        agg_key = round(aggression * 10) / 10
        if agg_key not in results["runs_by_aggression"]:
            results["runs_by_aggression"][agg_key] = []
            results["wickets_by_aggression"][agg_key] = 0
        results["runs_by_aggression"][agg_key].append(run)
        if out:
            results["wickets_by_aggression"][agg_key] += 1
        
        # Track by settle meter (in buckets of 10)
        settle_key = int(settle_meter / 10) * 10
        if settle_key not in results["runs_by_settle"]:
            results["runs_by_settle"][settle_key] = []
            results["wickets_by_settle"][settle_key] = 0
        results["runs_by_settle"][settle_key].append(run)
        if out:
            results["wickets_by_settle"][settle_key] += 1
    
    # Display results
    analyze_ball_data_results(results, match_format, num_balls)

def analyze_ball_data_results(results, match_format, num_balls):
    """Analyze and display ball simulation results."""
    print(f"\n==== Ball-by-Ball Analysis ({match_format.upper()}) ====")
    
    # Basic statistics
    total_runs = sum(results["runs"])
    run_rate = total_runs / (num_balls/6)
    dot_percentage = (results["dot_balls"] / num_balls) * 100
    boundary_percentage = ((results["boundaries"]["fours"] + results["boundaries"]["sixes"]) / num_balls) * 100
    
    print(f"\nBasic Statistics:")
    print(f"Total runs: {total_runs}")
    print(f"Run rate: {run_rate:.2f}")
    print(f"Total wickets: {results['wickets']}")
    print(f"Wickets per over: {(results['wickets'] / (num_balls/6)):.2f}")
    print(f"Dot ball percentage: {dot_percentage:.1f}%")
    print(f"Boundary percentage: {boundary_percentage:.1f}%")
    
    # Run distribution
    print("\nRun Distribution:")
    for run, count in results["run_distribution"].items():
        percentage = (count / num_balls) * 100
        bar = "#" * int(percentage/2)
        print(f"{run} runs: {percentage:.1f}% {bar} ({count})")
    
    # Aggression analysis
    print("\nRuns by Aggression Level:")
    for agg, runs in sorted(results["runs_by_aggression"].items()):
        avg_run = sum(runs) / len(runs) if runs else 0
        wickets = results["wickets_by_aggression"][agg]
        wicket_rate = (wickets / len(runs)) * 100 if runs else 0
        print(f"Aggression {agg:.1f}: Avg runs {avg_run:.2f}, Wicket rate {wicket_rate:.1f}%")
    
    # Settle meter analysis
    print("\nPerformance by Settle Meter:")
    for settle, runs in sorted(results["runs_by_settle"].items()):
        avg_run = sum(runs) / len(runs) if runs else 0
        wickets = results["wickets_by_settle"][settle]
        wicket_rate = (wickets / len(runs)) * 100 if runs else 0
        print(f"Settle {settle}-{settle+9}: Avg runs {avg_run:.2f}, Wicket rate {wicket_rate:.1f}%")
    
    # Recommendations based on format
    print("\nRecommendations:")
    if match_format == "t20":
        if run_rate < 7.5:
            print("- T20 run rate is too low. Consider increasing batting effectiveness.")
        elif run_rate > 9.5:
            print("- T20 run rate is too high. Consider decreasing batting effectiveness.")
        
        if dot_percentage < 30:
            print("- T20 dot ball percentage is low. Consider increasing bowler dominance.")
        elif dot_percentage > 50:
            print("- T20 dot ball percentage is high. Consider decreasing bowler dominance.")
        
        if boundary_percentage < 15:
            print("- T20 boundary percentage is low. Consider boosting boundaries.")
        elif boundary_percentage > 25:
            print("- T20 boundary percentage is high. Consider reducing boundaries.")
    
    elif match_format == "odi":
        if run_rate < 5:
            print("- ODI run rate is too low. Consider increasing batting effectiveness.")
        elif run_rate > 7:
            print("- ODI run rate is too high. Consider decreasing batting effectiveness.")
        
        # Similar recommendations for ODI format
    
    else:  # test
        if run_rate < 3:
            print("- Test run rate is too low. Consider increasing batting effectiveness.")
        elif run_rate > 4:
            print("- Test run rate is too high. Consider decreasing batting effectiveness.")
        
        # Similar recommendations for Test format

# Run the bot
# For analyzing multiple match simulations
run_simulation_analysis(num_simulations=10, match_format="t20")

# For analyzing individual ball data
collect_ball_data(match_format="t20", num_balls=1000)