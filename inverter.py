#!/usr/bin/env python

import zlib
import hashlib
from os.path import getsize
from sys import argv
from math import ceil
import random


def get_hex_string(num):
	hex = "%x" % num
	if len(hex) % 2 != 0:
		hex = '0' + hex
	return hex

def pad(s, pad_char, width):
	return (width - len(s)) * pad_char + s

def reduce_for_table(idx):
	def reduce_using_ext(ext):
		def reduce_hash(hash):
			hex_digest = hashlib.md5(idx + ext + hex(hash)).hexdigest().decode('hex')[:3:]
			reduced = pad(hex_digest, '\x00', 3)
			assert(len(reduced) == 3), reduced
			return reduced
		return reduce_hash
	return reduce_using_ext

def to_bytes(num):
	return get_hex_string(num).decode('hex')

def to_num(bytes):
	return int(bytes.encode('hex'), 16)

#### GENERAL CONFIGURATION ####
INPUT_FILE = 'SAMPLE_INPUT.data'
TAIL_HASH_LEN = 3
HASH_MASK = (1 << ((TAIL_HASH_LEN * 8) - 1)) - 1
assert(bin(HASH_MASK).count('1') == ((TAIL_HASH_LEN * 8) - 1)), bin(HASH_MASK)
IS_DEBUG = False
## MAIN ADJUSTMENT PARAMETERS ##
CHAIN_LENGTH = int(argv[2])
NUM_TABLES = 2
################################
NUM_REDUCE_FNS = CHAIN_LENGTH
SUCCESS_RATE = 0.901
UNIQ_WORDS_PER_TABLE = int(ceil(pow(2, 24) * (1 - pow((1-SUCCESS_RATE), 1/float(NUM_TABLES)))))
RAINBOW_TABLES = [("v2_hash_len_%d_chain_len_%d_reduce_%d_table_%d_of_%d" % (TAIL_HASH_LEN, CHAIN_LENGTH, NUM_REDUCE_FNS, i+1, NUM_TABLES)) for i in range(NUM_TABLES)]
REDUCE_FUNCTIONS_FOR_TABLES = [reduce_for_table(str(i)) for i in range(NUM_TABLES)]
REDUCE_FUNCTIONS = map(lambda rdc_fn_for_table: [rdc_fn_for_table(str(i)) for i in range(NUM_REDUCE_FNS)], REDUCE_FUNCTIONS_FOR_TABLES)


class PRNG:
	def __init__(self, seed):
		random.seed(seed)
		self.past_values = set()

	def advance_state(self):
		self.state = pad((get_hex_string(random.getrandbits(24))).decode('hex'), '\x00', 3)
		return self.state

	def get_next(self):
		"""Returns a pseudorandom 3-bytes word that has not been returned before
		"""
		assert(len(self.past_values) < 256**3)
		while self.advance_state() in self.past_values:
			pass
		self.past_values.add(self.state)
		return self.state

class Inverter:
	def __init__(self):
		self.mask = HASH_MASK
		self.sha1_calls = 0
		self.num_of_void_bytes = 0
		self.tables = {}
		self.parse_tables()
		self.reduce_functions = REDUCE_FUNCTIONS # functions that reduce a sha1 hash into a 3-byte string

	def get_sha1_calls(self):
		return self.sha1_calls

	def get_num_of_void_bytes(self):
		return self.num_of_void_bytes

	def sha1(self, s):
		"""Returns the integer representation of the string s' sha1 hash

		s: the string to be hashed
		"""
		self.sha1_calls += 1
		return int(hashlib.sha1(s).hexdigest(), 16)

	def parse_table(self, table_idx):
		table_name = RAINBOW_TABLES[table_idx]
		prng = PRNG(table_idx)
		this_chain = {}
		with open(table_name, 'rb') as f:
			# populate this_chain
			first_byte = f.read(1)
			while first_byte != '':
				current_word = prng.get_next()
				first_byte_i = int(first_byte.encode('hex'), 16)
				is_voided = False if (first_byte_i & 128) == 0 else True
				if is_voided:
					self.num_of_void_bytes += 1
					# skip over certain number of RNG values
					num_of_skips = (first_byte_i & 127) - 1
					for i in range(num_of_skips):
						prng.get_next()
				else:
					hash = first_byte + f.read(TAIL_HASH_LEN - 1)
					this_chain[int(hash.encode('hex'), 16)] = current_word
				first_byte = f.read(1)
		self.tables[table_idx] = this_chain

	def parse_tables(self):
		for i in range(NUM_TABLES):
			self.parse_table(i)

	def get_reduced(self, hashes, reduce_functions, iterations):
		assert(len(hashes) == len(reduce_functions))
		c = iterations
		reduced = hashes[::]
		for offset in range(len(hashes)):
			reduce_fn = reduce_functions[(offset + c) % len(reduce_functions)]
			reduced[offset] = reduce_fn(hashes[offset])
		return reduced

	def get_matches(self, list_of_full_hashes, haystack):
		matching_substrings = set()
		hash_substrings = map(lambda hash: hash & self.mask, list_of_full_hashes)
		for hash_substring in hash_substrings:
			if hash_substring in haystack:
				matching_substrings.add(hash_substring)
		return matching_substrings


	def search_chain(self, matching_hash_substring, hash, chains, reduce_functions, searched):
		current_word = chains[matching_hash_substring]
		current_hash = self.sha1(current_word)
		for i in range(CHAIN_LENGTH - (searched - 1)):
			if current_hash == hash:
				return current_word.encode('hex')
			reduce_fn = reduce_functions[i % len(reduce_functions)]
			current_word = reduce_fn(current_hash)
			current_hash = self.sha1(current_word)
		return False

        def invert(self, hash):
                """Returns a word that hashes to hash or '0' if the word cannot be found

                hash: integer value of hash
                """
		assert(CHAIN_LENGTH == NUM_REDUCE_FNS), "This fn was designed with CHAIN_LENGTH == NUM REDUCE FNS in mind!"

                searched_chains = {}
                current_hash = {}

                for i in xrange(NUM_TABLES):
                        searched_chains[i] = set()
                        current_hash[i] = hash

                for search_pos in xrange(CHAIN_LENGTH + 1):
                        for table_idx in xrange(NUM_TABLES):
                                current_hash[table_idx] = hash
                                for i in xrange(CHAIN_LENGTH - search_pos, CHAIN_LENGTH):
                                        reduce_fn = self.reduce_functions[table_idx][i]
                                        word = reduce_fn(current_hash[table_idx])
                                        current_hash[table_idx] = self.sha1(word)
					if current_hash[table_idx] == hash:
						return word.encode('hex') # Xinan's idea of a surprise :O

                                tail_hash = (current_hash[table_idx] & self.mask)
                                if (tail_hash in self.tables[table_idx]) and (tail_hash not in searched_chains[table_idx]):
                                        result = self.search_chain(tail_hash, hash, self.tables[table_idx], self.reduce_functions[table_idx], search_pos)
                                        if result:
                                                return result
                                        searched_chains[table_idx].add(tail_hash)

                return '0'

def generate_rainbow_table(table_idx):
	total_words = set()
	added_hashes = set()
	prng = PRNG(table_idx)
	num_of_skips = 0
	table_name = RAINBOW_TABLES[table_idx]
	reduce_functions = REDUCE_FUNCTIONS[table_idx]
	with open(table_name, 'wb') as f:
		total_skipped_bytes = 0
		while len(total_words) < UNIQ_WORDS_PER_TABLE:
			word = prng.get_next()
			has_collision = False
			words_in_chain = set()
			for i in range(CHAIN_LENGTH):
				hash = int(hashlib.sha1(word).hexdigest(), 16)
				words_in_chain.add(word)
				reduce_fn = reduce_functions[i % NUM_REDUCE_FNS]
				word = reduce_fn(hash)

			hash = int(hashlib.sha1(word).hexdigest(), 16)
			if (hash & HASH_MASK) in added_hashes:
				has_collision = True

			if (has_collision and num_of_skips >= 127) or (not has_collision and num_of_skips > 0):
				# flush any unwritten collision records to file
				assert(num_of_skips < 128)
				f.write(bytearray([128 | num_of_skips]))
				num_of_skips = 0

				if IS_DEBUG:
					total_skipped_bytes += 1
					print "[!] Skipped a chain when number of used words is %d" % len(total_words)
					print "[!] Total bytes wasted due to skipped chains: %d" % total_skipped_bytes

			if has_collision:
				num_of_skips += 1
			else:
				total_words.update(words_in_chain)
				# write this chain to file
				hash_substring_i = (hash & HASH_MASK)
				added_hashes.add(hash & HASH_MASK)
				bytes = pad((get_hex_string(hash_substring_i)).decode('hex'), '\x00', TAIL_HASH_LEN)
				assert(len(bytes) == TAIL_HASH_LEN), bytes.encode('hex')
				f.write(bytes)

def generate_rainbow_tables():
	for i in range(NUM_TABLES):
		generate_rainbow_table(i)

def get_grade(F, S):
	if S <= 2000000 and F >= 100:
		return int( min(18, (2.0 ** 30 * F / S ** 2 - 1.1) * 7 + 18) )
	return 0

def get_compressed_size(files):
	concat_files = ''
	for filename in files:
		with open(filename, 'r') as f:
			concat_files += f.read()
	return len(zlib.compress(concat_files, 9))

def invert_input(inverter):
	"""Inverts sha1 hashes from INPUT_FILE."""
	num_lines = 0
	num_found = 0
	S = min(get_compressed_size(RAINBOW_TABLES), sum([getsize(table) for table in RAINBOW_TABLES]))
	with open(INPUT_FILE, 'r') as f:
		for line in f:
			num_lines += 1
			hash = int(''.join(line.split()), 16)
			word = inverter.invert(hash)
			if word != '0':
				num_found += 1
			print word.upper()
			if IS_DEBUG:
				F = ((num_lines * (1<<23))/inverter.get_sha1_calls())
				print "[+] Chain length: %d" % CHAIN_LENGTH
				print "[+] Number of reduce functions: %d" % NUM_REDUCE_FNS
				print "[+] Number of tables: %d" % NUM_TABLES
				print "[+] Tail hash length: %d bytes" % TAIL_HASH_LEN
				print "[+] Size of rainbow table (S): %d bytes" % S
				print "[+] Speedup factor (F): %d" % F
				print "[+] Grade: %d" % get_grade(F, S)

	# Print test results
	print "The total number of words found is: %d" % num_found
	t = inverter.get_sha1_calls()
	C = (num_found/float(num_lines) * 100)
	F = ((5000 * 2**23)/inverter.get_sha1_calls())
	print "[+] Number of SHA1 calls (t): %d" % t
	print "[+] Percentage of words correctly inverted (C): %.2f%%" % C
	print "[+] Size of rainbow table (S): %d bytes" % S
	print "[+] Speedup factor (F): %d" % F
	print "[+] Number of void bytes: %d" % inverter.get_num_of_void_bytes()
	print "[+] Chain length: %d" % CHAIN_LENGTH
	print "[+] Number of reduce functions: %d" % NUM_REDUCE_FNS
	print "[+] Number of tables: %d" % NUM_TABLES
	print "[+] Tail hash length: %d bytes" % TAIL_HASH_LEN
	print "[+] Grade: %d" % get_grade(F, S)


if __name__ == "__main__":
	if 'debug' in map(lambda a: a.lower(), argv):
		IS_DEBUG = True

	if 'test' in argv:
		inverter = Inverter()
		invert_input(inverter)
	elif 'generate' in argv:
		generate_rainbow_tables()
	else:
		print "Usage: python inverter.py [generate/test] chain_length"
