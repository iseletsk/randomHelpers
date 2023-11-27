import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import json

TEST_MODE = False


with open('credentials/alma_members.json', 'r') as f:
    creds = json.load(f)
    MEMBERSHIP_MASTER = creds['spreadsheet_id'] # spreadsheet ID

def get_members(tab):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials/driveautomation-354723-abc919c39f3b.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_key(MEMBERSHIP_MASTER).worksheet(tab)
    data = wks.get_all_values()
    return data


INDIVIDUAL_TAB = "AlmaLinux Individual Application"
MIRROR_TAB = "AlmaLinux Mirror Contributor Application"
SPONSOR_TAB = "AlmaLinux Sponsorship Application"


# approval, email, name, nick, address, timestamp
COLUMN_NAMES=['approval', 'email', 'name', 'nick', 'address', 'timestamp']
INDIVIDUAL_COLS = ['G', 'N', 'O', 'P', 'Q', 'M']
MIRROR_COLS = ['B', 'L', 'J', 'H', 'I', 'G']
SPONSOR_COLS = ['A', 'K', 'I', 'G', 'H', 'F']



def c2n(c):
    return ord(c.upper()) - 65

def col2val(row, cols, column_name):
    return row[c2n(cols[COLUMN_NAMES.index(column_name)])].strip()


APPROVED_MEMBER_HEADERS= ['E-Mail', 'Nick / Company', 'Name', 'Timestamp']

SPONSOR_CATEGORY_COL='O'
GOLD_FILTER=[(SPONSOR_CATEGORY_COL, 'gold')]
SILVER_FILTER=[(SPONSOR_CATEGORY_COL, 'silver')]
PLATINUM_FILTER=[(SPONSOR_CATEGORY_COL, 'platinum')]
def approved_members(tab, cols, include_no_email=False, field_filter=None):
    data = get_members(tab)
    approved = []
    for row in data:
        if 'approved' in str.lower(col2val(row, cols, 'approval')):
            if field_filter:
                is_ok = True
                for f in field_filter:
                    is_ok = is_ok and row[c2n(f[0])].lower().startswith(f[1])
                if not is_ok:
                    continue
            nick = col2val(row, cols, 'nick')
            email = col2val(row, cols, 'email')
            if email != '' or include_no_email:
                approved.append([email, nick, col2val(row, cols, 'name'),
                                 col2val(row, cols, 'timestamp')])
    return approved


def get_individual(include_no_email=False):
    return approved_members(INDIVIDUAL_TAB, INDIVIDUAL_COLS, include_no_email=include_no_email)


def get_mirror(include_no_email=False):
    return approved_members(MIRROR_TAB, MIRROR_COLS, include_no_email=include_no_email)


def get_sponsor(include_no_email=False, field_filter=None):
    return approved_members(SPONSOR_TAB, SPONSOR_COLS, include_no_email=include_no_email, field_filter=field_filter)


def name_to_id(name):
    return "".join(c for c in name if c.isalnum())


def to_helios_row(row):
    email = row[0]
    nick =  row[1]
    if not nick:
        nick = str.strip(row[2])
    if TEST_MODE:
        email = 'iseletsk+testelect@gmail.com'
    return ['password', name_to_id(nick), email, nick]

def to_sendgrid_row(row):
    email = row[0]
    nick =  row[1]
    if not nick:
        nick = str.strip(row[2])
    if TEST_MODE:
        email = 'iseletsk+testelect@gmail.com'
    return [email, row[1]]


DEST = '/Users/iseletsk/Downloads/'
def write_voters(filename, voters):
    with open(DEST + filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for row in voters:
            writer.writerow(row)

def write_voters_helios(filename, voters):
    with open(DEST + filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for row in voters:
            writer.writerow(to_helios_row(row))
def to_csv():
    individuals = get_individual()
    print("Individuals: {}".format(len(individuals)))
    mirrors = get_mirror()
    print("Mirrors: {}".format(len(mirrors)))
    silver_sponsors = get_sponsor(field_filter=SILVER_FILTER)
    gold_sponsors = get_sponsor(field_filter=GOLD_FILTER)
    platinum_sponsors = get_sponsor(field_filter=PLATINUM_FILTER)
    print("Silver Sponsors: {}".format(len(silver_sponsors)))
    print("Gold Sponsors: {}".format(len(gold_sponsors)))
    print("Platinum Sponsors: {}".format(len(platinum_sponsors)))

    write_voters_helios('MembersAndMirrors.csv', individuals + mirrors)
    write_voters_helios('SilverSponsors.csv', silver_sponsors)
    write_voters_helios('GoldSponsors.csv', gold_sponsors)
    write_voters_helios('PlatinumSponsors.csv', platinum_sponsors)

    write_voters('all_members.csv', individuals + mirrors + silver_sponsors + gold_sponsors + platinum_sponsors)
    write_voters('individual-filtered.csv', individuals)
    write_voters('mirrors-filtered.csv', mirrors)
    write_voters('sponsors-filtered.csv', silver_sponsors + gold_sponsors + platinum_sponsors)

    # approval, email, name, nick, address, timestamp
    with open('/Users/iseletsk/Downloads/members-for-election-committee.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        r = APPROVED_MEMBER_HEADERS + ['Member Type']
        writer.writerow(r)
        for row in individuals:
            r = row + ['individual']
            writer.writerow(r)
        for row in mirrors:
            r = row + ['mirror']
            writer.writerow(r)
        for row in silver_sponsors+gold_sponsors+platinum_sponsors:
            r = row + ['sponsor']
            writer.writerow(r)



to_csv()
