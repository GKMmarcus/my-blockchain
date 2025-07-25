import hashlib, json, sys, random, copy
random.seed(0)

#Our Hash Function
def hashMe(msg = ""):
    if type(msg)!=str:
        msg = json.dumps(msg,sort_keys=True)
    
    if sys.version_info.major == 2:
        return unicode(hashlib.sha256(msg).hexdigest(), 'utf-8')
    else:
        return hashlib.sha256(str(msg).encode('utf-8')).hexdigest()

#Create a random transaction between Alice and Bob
def makeTransaction(maxValue=3):
    sign = int(random.getrandbits(1))*2 - 1 

    amount = random.randint(1,maxValue)
    alicePays  = sign * amount
    bobPays = -1 * alicePays

    return {u'Alice':alicePays, u'Bob': bobPays}

txnBuffer = [makeTransaction() for i in range(30)]

#Apply a transaction to the current state and return the updated state
def updateState(txn, state):
    state = state.copy()

    for key in txn:
        if key in state.keys():
            state[key] += txn[key]
        else:
            state[key] = txn[key]
    return state

#Check if a transaction is valid
def isValidTxn(txn,state):
    if sum(txn.values()) != 0:
        return False
    
    for key in txn.keys():
        if key in state.keys():
            acctBalance = state[key]
        else:
            acctBalance = 0
        if (acctBalance + txn[key]) < 0:
            return False
    return True

#Define our initial
state = {u'Alice':50, u'Bob':50}

#Define our genesis block
genesisBlockTxns = [state]
genesisBlockContents = {u'blockNumber': 0,u'parentHash':None,u'txnCount':1,u'txns':genesisBlockTxns}
genesisHash = hashMe( genesisBlockContents )
genesisBlock ={u'hash':genesisHash,u'contents':genesisBlockContents}
genesisBlockStr = json.dumps(genesisBlock, sort_keys=True)

chain = [genesisBlock]

#Create a new block for the transaction
def makeBlock(txns,chain):
    parentBlock = chain[-1]
    parentHash = parentBlock[u'hash']
    blockNumber = parentBlock[u'contents'][u'blockNumber'] + 1
    blockContents = {u'blockNumber': blockNumber, u'parentHash': parentHash, u'txnCount':len(txns),"txns":txns}
    blockHash = hashMe(blockContents)
    block = {u'hash':blockHash,u'contents':blockContents}

    return block

blockSizeLimit = 5
while len(txnBuffer) > 0:
    bufferStartSize = len(txnBuffer)

    txnList = []
    while (len(txnBuffer)>0) & (len(txnList) < blockSizeLimit):
        newTxn = txnBuffer.pop()
        validTxn = isValidTxn(newTxn,state)

        if validTxn:
            txnList.append(newTxn)
            state = updateState(newTxn,state)
        else:
            print ('Ignored transaction')
            sys.stdout.flush()
            continue

    myBlock = makeBlock(txnList,chain)
    chain.append(myBlock)

#Make sure the block contents match
def checkBlockHash(block):
    expectedHash = hashMe( block['contents'])
    if block['hash'] != expectedHash:
        raise Exception('Hash does not match contents of block%s' % block['contents']['blockNumber'])
    return

#Validate the block and update the state
def checkBlockVaildity(block,parent,state):
    parentNumber = parent['contents']['blockNumber']
    parentHash = parent['hash']
    blockNumber = block['contents']['blockNumber']

    for txn in block['contents']['txns']:
        if isValidTxn(txn,state):
            state = updateState(txn,state)
        else:
            raise Exception('Invalid transaction in block %s: %s'%(blockNumber,txn))
    
    checkBlockHash(block)

    if blockNumber!=(parentNumber+1):
        raise Exception('Hash does not match contents of block %s'%blockNumber)
    
    if block['contents']['parentHash'] != parentHash:
        raise Exception('Parent hash not accurate at block %s'%blockNumber)
    
    return state

#Check valididty of the entire blockchain
def checkChain(chain):
    if type(chain)==str:
        try:
            chain = json.loads(chain)
            assert( type(chain)==list)
        except:
            return False
    elif type(chain)!=list:
        return False

    state = {}

    for txn in chain[0]["contents"]['txns']:
        state = updateState(txn,state)
    checkBlockHash(chain[0])
    parent = chain[0]

    for block in chain[1:]:
        state = checkBlockVaildity(block,parent,state)
        parent = block

    return state

#Creating the Output
nodeBchain = copy.copy(chain)
nodeBtxns = [makeTransaction() for i in range(5)]
newBlock = makeBlock(nodeBtxns,nodeBchain)

print("Blockchain on Node A is currently %s blocks long"%len(chain))

try:
    print("New Block Received; checking validity...")
    state = checkBlockVaildity(newBlock,chain[-1],state)
    chain.append(newBlock)
except:
    print('Invaild block; ignoring and waiting for the next block...')

print("Blockchain on Node A is now %s blocks long"%len(chain))