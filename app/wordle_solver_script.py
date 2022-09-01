"""
Wordle solver 
By Chris Grylls
V2: separated all functionality into functions

TODO:
- command: all
    print all remaining words
- consider how common words are
    if they occur below a threshold, move them to the back of the list of suggested words
    only once we're down to ~10 words left, or a certain number of guesses left

the dictionary wordle uses to check words against is CSW19
https://github.com/scrabblewords/scrabblewords/blob/main/words/British/CSW19.txt
"""
# -----------------------------------------------
# IMPORTS
# -----------------------------------------------
import string   #for alphabet
import operator #for sorting list of classes by attribute
import pprint
from collections import defaultdict #for another way to order letter counts :/
import json


# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------
def import_english_dict(eng_dict_path, WORD_LEN):
        
    # import english dictionary
    with open(eng_dict_path) as file:
            orig_word_list = list(file.read().split())

    # cut down to 5 letter words only
    all_five_letter_words  = [w for w in orig_word_list if len(w) == WORD_LEN]
    word_list = all_five_letter_words.copy()

    return word_list

def valid_result(result):
    valid_results = ['-', 'Y', 'G', 'y', 'g']
    
    if len(result) != WORD_LEN: return False
    
    for letter in result:
        if letter not in valid_results: return False
    
    return True


    # all_letters = {
    #     'grey': set(),
    #     'yellow': set(),
    #     'green': set()

        # letters = {
        #     'grey': set(),
        #     'yellow': set(),
        #     'green': set()
        # }


def update_valid_letters(guess, result, letters, all_letters):
        # understand which letters are yellow/green/not
    for i, letter in enumerate(guess):
        if result[i] == 'G': 
            letters['green'].add((letter, i))
            all_letters['green'] =  all_letters['green'].union(letters['green']) #update full list
        elif result[i] == 'Y': 
            letters['yellow'].add((letter, i))
            all_letters['yellow'] = all_letters['yellow'].union(letters['yellow']) #update full list

        elif result[i] == '-': 
            
            # don't do this assessment if the letter is also yellow at this step
            try: yellow_letters_only, _ = zip(*letters['yellow']) #try except incase there are no letters in yellow yet
            except ValueError: yellow_letters_only = []
            
            if not letter in yellow_letters_only:

                # add grey letter at every position, unless it is in specific green position, or in a duplicate letter's position, or in any yellow position
                duplicate_letters = [l for l in string.ascii_lowercase if guess.count(l) >= 2]
                grey_rem = set()
                if len(duplicate_letters) != 0: #only if there is a duplicate letter
                    for dup in duplicate_letters:
                        for j, l in enumerate(guess):
                            if l == dup:
                                grey_rem.add((l, j))
                    try: grey_rem.remove((letter, i)) #remove the current (we only want the other letter's position here, since we'll exclude it later)
                    except KeyError: pass #try-except, incase we try to remove nothing
                
                grey_add = {(letter, k) for k in range(WORD_LEN)}
                for tup in grey_rem:
                    try: grey_add.remove(tup)
                    except KeyError: pass #try-except, incase we try to remove nothing

                
                try: grey_add.remove(grey_add.intersection(all_letters['green'])) #remove any in green
                except KeyError: pass #try-except, incase we try to remove nothing
                

                letters['grey'] = letters['grey'].union(grey_add)
                all_letters['grey'] = all_letters['grey'].union(letters['grey']) #update full list

                # # don't add grey letter if letter still in yellow
                # if all_letters['yellow'] != set(): # make sure all_letters['yellow'] is not empty
                #     y_letts_only, _ = zip(*all_letters['yellow'])
                #     if letter in y_letts_only: grey_add = set()



        # they are sets, so duplicates won't be added

    #remove any grey letters that are in green
    try: all_letters['grey'].remove(all_letters['grey'].intersection(all_letters['green'])) #remove any in green
    except KeyError: pass #try-except, incase we try to remove nothing
    try: letters['grey'].remove(letters['grey'].intersection(all_letters['green'])) #remove any in green
    except KeyError: pass #try-except, incase we try to remove nothing

    #remove any green letters that are in grey
    try: all_letters['green'].remove(all_letters['green'].intersection(all_letters['grey'])) #remove any in green
    except KeyError: pass #try-except, incase we try to remove nothing
    try: letters['green'].remove(letters['green'].intersection(all_letters['grey'])) #remove any in green
    except KeyError: pass #try-except, incase we try to remove nothing

    return letters, all_letters

def assess_words(wl, letter_set, l_type):
    temp_word_list = wl.copy() #create temp copy so we're not iterating and modifying the same list
    for word in temp_word_list:
        for letter, i in letter_set:
            if l_type == 'G': #remove word if letter does *not* occur at given position
                if word[i] == letter: 
                    pass #keep it
                else:
                    try: wl.remove(word)
                    except ValueError: pass #try-except, since word may have already been removed when iterating through letters

            elif l_type == 'Y': #remove word if letter occurs at given position
                if word[i] != letter: 
                    pass #keep it
                else:
                    try: wl.remove(word)
                    except ValueError: pass #try-except, since word may have already been removed when iterating through letters      
                #remove word if it does not contain letter at all 
                #i.e. only keep words which contain the yellow letter
                if letter not in word:
                    try: wl.remove(word)
                    except ValueError: pass #try-except, since word may have already been removed when iterating through letters      
			
            elif l_type == '-': #remove word if letter occurs at given position
                if word[i] != letter: 
                    pass #keep it
                else:
                    try: wl.remove(word)
                    except ValueError: pass #try-except, since word may have already been removed when iterating through letters      
   
               
    return wl

def reduce_word_list(result, word_list, letters, printout=False): # assess_words() inside this
    # assess word_list (for current iteration)
    # order: grey, green, yellow
    # for grey letters
    if printout: print('After eliminating words based on:')
    if '-' in result: 
        word_list = assess_words(word_list, letters['grey'], '-')
        if printout: print(f'    new GREY letters, remains: {len(word_list)} words')

    # for green letters
    if 'G' in result: 
        word_list = assess_words(word_list, letters['green'], 'G')
        if printout: print(f'    new GREEN letters, remains: {len(word_list)} words')

    # for yellow letters
    if 'Y' in result: 
        word_list = assess_words(word_list, letters['yellow'], 'Y')
        if printout: print(f'    new YELLOW letters, remains: {len(word_list)} words')

    return word_list

def create_letter_dict(word_list):
    #setup letter dict
    letter_count_dict = {}
    for l in string.ascii_lowercase:
        letter_count_dict[l] = 0

    letter_dict = {}
    for i in range(5):
        letter_dict[i] = letter_count_dict.copy()

    #count of each letter in each slot for the remaining words
    for word in word_list:
        for i, letter in enumerate(word):
            letter_dict[i][letter] += 1
    
    return letter_dict

class Word_Counted:
    def __init__(self, word, letter_occurrences):
        self.word = word
        self.letter_sum = sum([letter_occurrences[i][l] for i, l in enumerate(self.word)])

def next_best_words(word_list, letter_dict):
    # for each word, sum the number of times that letter was counted in each position.
    # then sort the list 
    words_as_classes = [Word_Counted(word, letter_dict) for word in word_list]
    words_as_classes.sort(key=operator.attrgetter('letter_sum'), reverse=True)

    top_n_words = [w.word for w in words_as_classes[:20]] #only return top 20
    return top_n_words

def default_return_0():
    return 0

def order_by_likelihood(word_list, json_filename, printout=False):
    with open(json_filename) as json_obj:
        json_dict = json.load(json_obj)
    
    word_freq = json_dict['wordFreq']

    in_word_freq = {}
    not_in_word_freq = []
    for word in word_list:
        if word in word_freq.keys():
            in_word_freq[word] = word_freq[word]
        else: not_in_word_freq.append(word)
    
    sorted_in_word_freq = sorted(in_word_freq, key=in_word_freq.get)
    
    if printout:
        print()
        if sorted_in_word_freq == []:
            print('None of these words are very common!')
        else: pprint.pprint(in_word_freq, sort_dicts=False)
    
    return_list = sorted_in_word_freq + not_in_word_freq

    return return_list


def best_guess_to_whittle_down(word_list, all_five_letter_words):
# count the frequency of letters in all words remaining
    letter_count_dict_rems = defaultdict()
    joined_remaining = ''.join(word_list)
    for l in joined_remaining:
        letter_count_dict_rems[l] = joined_remaining.count(l)

    #order this dict
    least_common_letters = sorted(letter_count_dict_rems, key=letter_count_dict_rems.get)
    req_letters = least_common_letters[:len(word_list)]

    # iterate down the number of letters
    best_guess_words = []
    num_letters_to_match = WORD_LEN +1
    while best_guess_words == []:
        num_letters_to_match -=1
        for word in all_five_letter_words:
            if sum([l in req_letters for l in word]) == num_letters_to_match:
                best_guess_words.append(word)

    #put the words with unique letters first: remove and append, then reverse
    for word in best_guess_words: 
        if not any([word.count(l) > 1 for l in word]):
            best_guess_words.remove(word)
            best_guess_words.append(word)
    best_guess_words.reverse()

    return best_guess_words

#for debugging
def pp(letter_set):
    #take a letter set and pretty print it
    if letter_set == set():
        return_dict = 'EMPTY'
    else:
        letters_inside, _ = zip(*letter_set)
        return_dict = {}
        for l in letters_inside:
            #for each letter, get the slots its in from the letter_set
            ll = [tup[1] for tup in letter_set if l in tup]
            ll.sort()
            return_dict[l] = ll
    
    pprint.pprint(return_dict)


# -----------------------------------------------
# MAIN
# -----------------------------------------------
def main(WORD_LEN, eng_dict_path, NUM_WORDS_TO_RETURN):

    print()
    print('Welcome to wordle solver! by Chris Grylls')

    #import and cut down english dictionary
    word_list = import_english_dict(eng_dict_path, WORD_LEN)
    #keep a copy of all the 5 letter words
    all_five_letter_words = word_list.copy()

    print(f'Initial number of possible {WORD_LEN} letter words: {len(word_list)}')
    print('Starting word suggestions: audio, ...')

    # Starting loop 
    NUM_ATTEMPTS = 6
    attempt_no = 0
    solved = False

    # create sets
    all_letters = {
        'grey': set(),
        'yellow': set(),
        'green': set()
    }

    while attempt_no < NUM_ATTEMPTS:

        guess = ' '
        letters = {
            'grey': set(),
            'yellow': set(),
            'green': set()
        }

        # increment attempt number
        attempt_no += 1
        print()
        print('---')
        print(f'Attempt number: {attempt_no}')
        # print('Current data:')
        # print(f'GREEN:')
        # pp(all_letters['green'])
        # print(f'YELLOW:')
        # pp(all_letters['yellow'])
        # print(f'GREY:')
        # pp(all_letters['grey'])
        # print()

        # ask for word input
        while not guess.isalpha() or len(guess)!=WORD_LEN: #make sure '-' isn't in the word, it should only be letters, and its the correct length
            guess = input('Which word did you input? ').lower()

        # result of first word
        result = '' #initialise

        # ask for result while it only consists of valid inputs
        while not valid_result(result):
            result = input('Result [-/Y/G]: ').upper()

        # break loop if all correct
        if result == 'G'*WORD_LEN:
            solved = True
            break

        # understand which letters are yellow/green/not
        letters, all_letters = update_valid_letters(guess, result, letters, all_letters)

        #TEMP: to show us what letters are yellow/green/not this iter
        # print(f'new GREEN:')
        # pp(letters['green'])
        # print(f'new YELLOW:')
        # pp(letters['yellow'])
        # print(f'new GREY:')
        # pp(letters['grey'])

        # assess word_list (for current iteration)
        word_list = reduce_word_list(result, word_list, letters, printout=True)

        #then figure out what entry would eliminate the most words
        # find the most common letters in each spot

        # create letter_dict
        letter_dict = create_letter_dict(word_list)

        # letter_dict tells us how often a letter appears in each position for the remaining word_list 
        # but we need an actual word though
        top_words = next_best_words(word_list, letter_dict)

        # when theres less than 15 words left, order the words by most likely
        FIVE_LETTER_WORD_FREQ = r"C:\Users\chris\Documents\Python Scripts\Wordle Solver\dictionaries\5_letter_word_freq.json"
        if len(top_words) <= 15:
            top_words = order_by_likelihood(top_words, FIVE_LETTER_WORD_FREQ, printout=True)

        print(f'Next {len(top_words[:NUM_WORDS_TO_RETURN])} best words are: {top_words[:NUM_WORDS_TO_RETURN]}')

        # if we get stuck with only a single letter left to find:
        if result.count('G') >= WORD_LEN - 2:
            print()
            print('Finding words which will whittle this down...')

            best_guess_words = best_guess_to_whittle_down(word_list, all_five_letter_words)
            
            print()
            print(f'Try these words: {best_guess_words[:7]}')

    
    if solved:
        print()
        print('Congratulations for solving todays wordle!')

    else: 
        print()
        print('Unlucky! We didn\'t get it this time :(')
        print()
        print(f'It must be one of these words ({len(word_list)}):')
        for w in word_list: print(w)



#VARIABLES
if __name__ == '__main__':
    WORD_LEN = 5
    eng_dict_path = r"C:\Users\chris\Documents\Python Scripts\Wordle Solver\dictionaries\words_alpha.txt" 
    NUM_WORDS_TO_RETURN = 7
    main(WORD_LEN, eng_dict_path, NUM_WORDS_TO_RETURN)

