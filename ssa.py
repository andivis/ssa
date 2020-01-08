import logging
import os
import json
from collections import OrderedDict
import helpers

class Ssa:
    def run(self):
        self.initialize()

        files = os.listdir(self.inputDirectory)

        for file in files:
            self.onItemIndex = 0
            self.outputFileName = ''

            fileContents = helpers.getFile(os.path.join(self.inputDirectory, file))
            lines = fileContents.splitlines()

            self.startFile(file)

            for item in lines:
                self.showStatus(file, item, len(files), len(lines))
                self.doItem(item, file)                
                
            self.finishFile(self.outputFileName)

            self.onFileIndex += 1

        self.cleanUp()

    def doItem(self, item, file):
        try:
            record = self.parse(item)

            if record:
                self.output(record)
        except Exception as e:
            logging.error(f'Skipping. Something went wrong.')
            logging.error(e)

    def startFile(self, file):
        self.outputFileName = os.path.join(self.outputDirectory, file)
        # make the file empty
        open(self.outputFileName, 'w').close()

    def finishFile(self, fileName):
        file = helpers.getFile(fileName)

        # remove final newline character
        if file.endswith('\n'):
            file = file[0:-1]
            helpers.toFile(file, self.outputFileName, '')

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
        length = field['format'].get('length', '')

        if not result:
            result = field.get('defaultValue', '')

        if field.get('mustBeBlank', ''):
            result = ''
            padCharacter = field['format'].get('padChar', ' ')
            result = self.pad(result, padCharacter, length)

        if field.get('digitsAllowed', True) == False:
            result = self.removeNumbers(result)

        for c in field.get('disallowedCharacters', ''):
            if c in result:
                logging.error(f'Found {c} in {result}. That character is not allowed in {name}.')
                result = result.replace(c, '')

        for s in field.get('disallowedPrefixes', ''):
            if result.lower().startswith(f'{s} '):
                logging.error(f'{result} starts with "{s} ". That prefix is not allowed in {name}.')
                result = self.fixInvalid(result, f'{s} ', True)                    

        for s in field.get('disallowedSuffixes', ''):
            if result.lower().rstrip().endswith(f' {s}'):
                logging.error(f'{result} ends with " {s}". That suffix is not allowed in {name}.')
                result = self.fixInvalid(result, f' {s}', False)                    

        # too long?
        if len(result) > length:
            logging.error(f'{result} is too long for field {name}. Shortening it.')
            result = result[0:length]

        # too short
        if len(result) < length:
            padCharacter = field['format'].get('padChar', ' ')
            result = self.pad(result, padCharacter, length)

        if not self.isValid(field, result):
            return ''

        #debug
        if '0' in result:
            x = 2
        
        return result

    def removeNumbers(self, s):
        return ''.join(filter(lambda x: not x.isdigit(), s))

    def isValid(self, field, value):
        result = True

        name = field.get('name', '')

        mustBeLength = field.get('mustBeLength', '')

        if mustBeLength != '':
            lengthWithoutSpaces = len(value.replace(' ', ''))

            if lengthWithoutSpaces != mustBeLength:
                logging.error(f'{name} must be {mustBeLength} characters')
                return False

        if field.get('mustContainAtLeastOneCharacter', ''):
            lengthWithoutSpaces = len(value.replace(' ', ''))

            if lengthWithoutSpaces == 0:
                logging.error(f'{name} field is blank')
                return False

        return result
     
    def fixInvalid(self, value, toRemove, fromStart):
        result = value

        if fromStart:
            result = result[len(toRemove):]
        else:
            result = result[0:-len(toRemove)]

        logging.info(f'Fixed. Removed {toRemove} from {value}.')

        return result;

    def pad(self, s, padCharacter, length):
        result = s
        
        for i in range(len(s), length):
            result += padCharacter

        return result

    def showStatus(self, file, item, fileCount, itemCount):
        logging.info(f'File {self.onFileIndex + 1} of {fileCount}: {file}. Item {self.onItemIndex + 1} of {itemCount}.')
        logging.info(f'Item: {item[0:50]}...')
        
        self.onItemIndex += 1

    def cleanUp(self):
        logging.info(f'Results written to {self.outputDirectory}')
        logging.info(f'Total errors: {self.errorCount}')
        logging.info(f'Done')
        input("Press enter to exit")

    def initialize(self):
        helpers.setUpLogging(True)

        logging.info('Starting\n')

        self.maps = {}

        for file in os.listdir('resources'):
            name = helpers.fileNameOnly(file, False)

            path = os.path.join('resources', file)
            
            map = json.loads(helpers.getFile(path))

            self.maps[name.upper()] = map

        self.onFileIndex = 0
        self.onItemIndex = 0
        self.errorCount = 0
        self.inputDirectory = 'input'
        self.outputDirectory = 'output'

        helpers.makeDirectory(self.outputDirectory)

ssa = Ssa()
ssa.run()