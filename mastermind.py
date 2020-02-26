#!/usr/bin/env python

#Solves the Praetorian challenge "Mastermind" and outputs my hash into hash.txt

import requests, json, sys, itertools, random
import numpy as np

__author__ = 'Gerrit Bryan'
__licence__ = 'MIT'
email = 'polenz.gerrit@gmail.com'
__email__ = email


#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV|
#Written by Praetorian 																		#|															#|														#|
r = requests.post('https://mastermind.praetorian.com/api-auth-token/', data={'email':email})#|
r.json()																					#|
headers = r.json()																			#|	
headers['Content-Type'] = 'application/json'												#|
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#This holds all of the information given to me and has one external method and one internal method
class Game:
	def __init__(self):
		self.numLevel = 1
		r = requests.get('https://mastermind.praetorian.com/level/1/', headers=headers)
		response = r.json()
		print('Level 1')
		self._next_level(response)

	#All of the level data from the response
	def _next_level(self, response): #Leading underscore because only called within Game class
		self.numGladiators = response['numGladiators']
		self.numGuesses = response['numGuesses']
		self.numRounds = response['numRounds']
		self.numWeapons = response['numWeapons']
		self.numRounds = response['numRounds']

	#Posts a guess and has specific reaction to response
	def MakeaGuess(self, guess):
		r = requests.post('https://mastermind.praetorian.com/level/' + str(self.numLevel) + '/', data=json.dumps({'guess':guess}), headers=headers)
		response = r.json()

		#If the guess was incorrect and there are still guesses left
		if 'response' in response:
			response = response['response']
			self.rightWeapon = response[0]
			self.rightGladiator = response[1]
			#This keeps looping MakeaGuess if answer incorrect in SolveRound()
			return True		

		#If the guess was correct and there are more rounds
		elif 'numGladiators' in response:
			self.numRounds -= 1
			print('Rounds Left: ', self.numRounds)

		#If the guess was correct and there are no more rounds
		elif 'message' in response:
			print(response['message'])

			#If finished save the hash and exit
			if 'hash' in response:
				r = requests.get('https://mastermind.praetorian.com/hash/', headers=headers)
				response = r.json()
				with open('hash.txt','w') as f:
					f.write(response['hash'])
				sys.exit()

			#Only executes if there was no hash
			#Increase level and update information
			self.numLevel += 1
			print('Level ',self.numLevel)
			r = requests.get('https://mastermind.praetorian.com/level/' + str(self.numLevel) + '/', headers=headers)
			response = r.json()
			self._next_level(response)
			#for SolveRound()
			return False

		#Handles errors and any possible unexpected responses
		else:
			print(response)
			if 'error' in response:
				if response['error'] == 'Too many guesses. Try again!' or response['error'] == 'Guess took too long, please restart game.':
					print('oops...trying again')
					r = requests.get('https://mastermind.praetorian.com/level/' + str(self.numLevel) + '/', headers=headers)
					response = r.json()
					self._next_level(response)
					return False
			sys.exit()

#basically the itertools.product() function with some removed functionality and no repeats in output
def AllCombosNoDupes(twoDarray):
	twoDarray = [tuple(row) for row in twoDarray]
	output = [[]]
	for row in twoDarray:
		output = [i + [j] for i in output for j in row if j not in i]
	for item in output:
		yield list(item)


#Only care about reducing number of weapons here
def GeneratePopulation(game):
	weapons = list(range(game.numWeapons))
	gladiators = game.numGladiators
	possibleCorrect = [weapons[:] for i in range(gladiators)]
	loops = 0
	BigElim = False

	#1.5 and usage of BigElim made this more consistent for me
	while loops < game.numGuesses - int(1.5 * gladiators) or not BigElim:
		#Generate the guess based on the pool
		permutation = []
		for i in range(gladiators):
			appended = False
			while not appended:
				weapon = random.choice(possibleCorrect[i])
				if weapon not in permutation:
					permutation.append(weapon)
					appended = True

		#Decrease pool based on the response
		game.MakeaGuess(permutation)
		if game.rightWeapon == 0:
			BigElim = True
			for i in range(gladiators):
				for weapon in permutation:
					if weapon in possibleCorrect[i]:
						possibleCorrect[i].remove(weapon)
		if game.rightGladiator == 0:
			for i in range(gladiators):
				if permutation[i] in possibleCorrect[i]:
					possibleCorrect[i].remove(permutation[i])
		loops += 1

	#Now that the number has been reduced we can get the "permutations" (kinda permutations not really)
	return AllCombosNoDupes(possibleCorrect)

#This is the main logic for solving the rounds
#
#My solution is adapted from Knuth's Five-guess algorithm found here
#
#https://en.wikipedia.org/wiki/Mastermind_(board_game)
#
#Steps in my algorithm are written in a comment starting with a number 1-7
def SolveRound(game):
	# 1. Create the set S of 1296 possible codes (1111, 1112 ... 6665, 6666)
	if game.numWeapons <= 10: #Solution if permutation is possible (best)
		S = itertools.permutations(range(game.numWeapons), game.numGladiators)
	else: #Solution when permutation takes too long (fastest)
		S = GeneratePopulation(game)

	#2. Start with initial guess
	guess = tuple([ i for i in range(game.numGladiators)])

	#3. Play the guess to get a response
	while game.MakeaGuess(guess): 
		#4. Remove from S any code that would not give the same response if it were the code
		Stemp =[]
		for permutation in S:
			numSameWeapon = 0
			numSameGladiator = 0
			for i in range(game.numGladiators):
				if guess[i] in permutation:
					numSameWeapon += 1
					if guess[i] == permutation[i]:
						numSameGladiator += 1
			if numSameWeapon == game.rightWeapon and numSameGladiator == game.rightGladiator:
				Stemp.append(permutation)
		S = Stemp		

		#5. Apply the minimax technique to use the guess which has the highest minimum number of
			#possibilities it will eliminate from S
		if len(S) > 1500:
			#Solution when S is too long (fastest)
			guess = random.choice(S)
		else:
			#Solution if S is short enough for time constraints (best)
			best = 0		
			for permutation in S:
				score = 0
				for other in S:
					score += len([i for i, j in zip(permutation, other) if i == j])
					score += len([i for i in permutation if i in other])
				if score > best:
					best = score
					guess = permutation

		#6. If the response was right from #3, the algorithm terminates
		#7. Repeat from step #3

#Runs SolveRound() until the level increases
def SolveLevel(game):
	numLevel = game.numLevel
	while numLevel == game.numLevel:
		SolveRound(game)
	
def main():
	requests.post('https://mastermind.praetorian.com/reset/', headers=headers)
	newGame = Game()
	while True: #Game class will always sys.exit() somehow so this is not bad
		SolveLevel(newGame)

if __name__ == '__main__':
	main()