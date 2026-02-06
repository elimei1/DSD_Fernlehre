
class SeqNumGenerator(object):
    _seq_num: int = 0
    MAX_SEQ_NUM: int = pow(2, 32)

    def getSeqNum(self) -> int:
        num = self._seq_num
        if self._seq_num + 1 > SeqNumGenerator.MAX_SEQ_NUM:
             self._seq_num = 0
        else:
            self.incSeqNum()
        return num

    def setSeqNum(self, num: int) -> None:
        self._seq_num = num

    def incSeqNum(self) -> None:
        self._seq_num += 1