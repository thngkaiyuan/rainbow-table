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



# Disclaimer

This program was customized for a school assignment and you may need to change it to suit your needs.
