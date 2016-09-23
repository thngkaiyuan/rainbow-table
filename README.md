# Rainbow Table

![image](https://cloud.githubusercontent.com/assets/10496851/18791100/f54048fc-81e3-11e6-8622-0db53bf93941.png)

This program (inverter.py) is a customizable generator/inverter that is able to generate rainbow tables of arbitrary hit rates (e.g. 90% for this assignment) and it is also able to parse these tables for real-time inversion of SHA1 hashes that are derived from 3-bytes words.



# Usage

To generate rainbow tables, we first need to customize the parameters in the program. Some of the customizable fields are:
-	INPUT_FILE: Name of file containing SHA1 hashes for inversion
-	TAIL_HASH_LEN: The number of bytes that we use to store the final hash of each chain
-	NUM_TABLES: The number of tables that we want to spread across
-	SUCCESS_RATE: The probability that a given hash will be successfully inverted
These fields can be found at the top of the program as seen below:

![image](https://cloud.githubusercontent.com/assets/10496851/18791242/7c957930-81e4-11e6-964f-04ada2967673.png)

After configuration, we can then execute the command `python inverter.py generate <desired chain length>` to begin the generation of the rainbow table(s).

To invert hashes, simply change the value of INPUT_FILE and run `python inverter.py test <chain length of generated table>`. Each hash from the input file will then be read and inverted sequentially, with the inverted words piped to standard output:

![image](https://cloud.githubusercontent.com/assets/10496851/18791295/bc7a578c-81e4-11e6-95e7-d81ffcde261a.png)


# Understanding How It Works

## Generating the Rainbow Table

### Generating the right number of chains

According to the desired success rate and the number of tables that we want to spread across, we can compute the number of unique words that we need in each table:

![image](https://cloud.githubusercontent.com/assets/10496851/18791417/3ce33c04-81e5-11e6-8b30-014a50d75544.png)

Rearranging the equation gives us:

![image](https://cloud.githubusercontent.com/assets/10496851/18791450/58f87fbc-81e5-11e6-9102-99e440214752.png)

This value is computed before the generation of the rainbow tables and the program will continue to generate chains of the specified length until this minimum number has been met for the table (we use a set to track all the unique words generated). 

### Compression Tricks

To reduce the size of the rainbow table, we do not keep the initial word of each chain. Instead, we use a pseudorandom number generator to generate a sequence of deterministic 3-bytes words that we use as the start of each chain. That way, we do not have to store the start of each chain since we can regenerate the same sequence during parsing of the table.

We also store only 3 bytes of the final hash for each chain, knowingly permitting collisions during hash inversion to take place to trade for precious space in the table.

Finally, to keep track of chains that are discarded during the generation process (i.e. if the final hash of the chain collides with another existing one in the table), I created a structure to represent valid and void bytes. The structures are as follows:

For a valid chain, the first bit would be 0, followed by values of the hash:

![image](https://cloud.githubusercontent.com/assets/10496851/18791488/7f0d40b6-81e5-11e6-943c-70967a09d2cc.png)

For a discarded chain, the first bit would be 1, followed by a 7-bits value indicating the number of consecutive discarded chains:

![image](https://cloud.githubusercontent.com/assets/10496851/18791515/9a7acc60-81e5-11e6-8ed7-18842018c5fc.png)

This technique helps to save a lot of space especially towards the end of the table generation when a lot of chains are discarded due to collisions with existing chains in the table. At its best, each “discarded byte” can represent up to 127 consecutive discarded chains. This can be made even better by having a variable sized structure to store more consecutive discarded chains. However, the need to do that did not arise as the existing technique was good enough to achieve full marks.

## Search Algorithm

After generating the table, the same program can be used to parse the data structure as and when is necessary to perform hash inversions.

For each given hash, we start by guessing the position of the hash from the tail of the chain, therefore checking to see if the resulting hash exists in the rainbow table. For example, we check for the following hashes at each iteration:

- Iteration 1:	`original hash`
- Iteration 2:	`sha1(last_reduce(original_hash))`
- Iteration 3:	`sha1(last_reduce(sha1(second_last_reduce(original_hash))))`
- Iteration 4:	…

If any of the hash produced above is found, we then search through the chain until the position that we guessed to check if the hash is indeed in the chain or if it is a collision. If the original hash is reproduced in the chain, we then return the word that produced the hash.



# Disclaimer

This program was customized for a school assignment and you may need to change it to suit your needs.
