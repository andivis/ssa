import logging
import os
import json
from collections import OrderedDict
import helpers

class Ssa:
    def run(self):
        self.initialize()

        items = helpers.getFile('input.txt')

        if not items:
            logging.error("Please put a file called input.txt next to this program and try again")

        for item in items.splitlines():
            self.showStatus(item)
            self.doItem(item)

        self.cleanUp()

    def doItem(self, item):
        try:
            record = self.parse(item)

            if record:
                self.output(record)
        except Exception as e:
            logging.error(f'Skipping. Something went wrong.')
            logging.error(e)

    def parse(self, item):
        recordType = item[0:2]

        if not recordType in self.maps:
            logging.info(f'Skipping. Record type is {recordType}.')
            return
        
        result = {}
        
        i = 0

        for field in self.maps[recordType]:
            name = field.get('name', '')
            
            length = field['format'].get('length', '')

            if length == '':
                continue

            if i + length >= len(item):
                break

            value = item[i:i + length]

            result[name] = value.strip()

            i += length

        return result

    def output(self, item):
        line = ''

        for field in self.maps['OUTPUT']:
            value = self.getField(field, item)

            if not value:
                logging.error(f'Skipping. Something went wrong.')
                self.errorCount += 1
                return

            line += value

        logging.info(f'Output line: {line[0:50]}...')
        helpers.appendToFile(line, self.outputFileName, '\n')

    def getField(self, field, item):
        result = ''
        
        name = field.get('name', '')

        result = item.get(name, '')

        if not result:
            result = field.get('defaultValue', '')

        length = field['format'].get('length', '')

        # too long?
        if len(result) > length:
            result = result[0:length]

        # too short
        if len(result) < length:
            padCharacter = field['format'].get('padChar', ' ')

            result = self.pad(result, padCharacter, length)

        if not self.isValid(field, result):
            return ''

        return result

    def isValid(self, field, value):
        result = True

        name = field.get('name', '')

        mustBeLength = field.get('mustBeLength', '')

        if mustBeLength != '':
            lengthWithoutSpaces = len(value.replace(' ', ''))

            if lengthWithoutSpaces != mustBeLength:
                logging.error(f'{name} must be {mustBeLength} characters')
                return False

        disallowedCharacters = field.get('disallowedCharacters', '')

        if disallowedCharacters:
            for c in disallowedCharacters:
                if c in value:
                    logging.error(f'Found {c} in {value}. That character is not allowed in {name}.')
                    return False;

        if field.get('mustContainAtLeastOneCharacter', ''):
            lengthWithoutSpaces = len(value.replace(' ', ''))

            if lengthWithoutSpaces == 0:
                logging.error(f'{name} field is blank')
                return False

        return result
                
    def pad(self, s, padCharacter, length):
        result = s
        
        for i in range(len(s), length):
            result += padCharacter

        return result

    def showStatus(self, item):
        sample = item[0:50]
        
        logging.info(f'On item {self.onItemIndex + 1}: {sample}...')
        
        self.onItemIndex += 1

    def cleanUp(self):
        file = helpers.getFile(self.outputFileName)

        # remove final newline character
        if file.endswith('\n'):
            file = file[0:len(file) - 1]
            helpers.toFile(file, self.outputFileName, '')

        logging.info(f'Results written to {self.outputFileName}')
        logging.info(f'Total errors: {self.errorCount}')
        logging.info(f'Done')
        input("Press enter to exit")

    def initialize(self):
        # clear the log file
        open('log.txt', 'w').close()

        helpers.setUpLogging(True)

        logging.info('Starting\n')

        self.maps = {}

        for file in os.listdir('resources'):
            name = helpers.fileNameOnly(file, False)

            path = os.path.join('resources', file)
            
            map = json.loads(helpers.getFile(path))

            self.maps[name.upper()] = map

        self.onItemIndex = 0
        self.errorCount = 0
        self.outputFileName = 'output.txt'

        # make the file empty
        open(self.outputFileName, 'w').close()

        self.inputItems = []

ssa = Ssa()
ssa.run()