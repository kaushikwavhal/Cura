from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import sys
import os
import struct
import time

from Cura.util import mesh

def _loadAscii(m, f):
	cnt = 0
	for lines in f:
		for line in lines.split('\r'):
			if 'vertex' in line:
				cnt += 1
	m._prepareFaceCount(int(cnt) / 3)
	f.seek(5, os.SEEK_SET)
	cnt = 0
	data = [None,None,None]
	for lines in f:
		for line in lines.split('\r'):
			if 'vertex' in line:
				data[cnt] = line.split()[1:]
				cnt += 1
				if cnt == 3:
					m._addFace(float(data[0][0]), float(data[0][1]), float(data[0][2]), float(data[1][0]), float(data[1][1]), float(data[1][2]), float(data[2][0]), float(data[2][1]), float(data[2][2]))
					cnt = 0

def _loadBinary(m, f):
	#Skip the header
	f.read(80-5)
	faceCount = struct.unpack('<I', f.read(4))[0]
	m._prepareFaceCount(faceCount)
	for idx in xrange(0, faceCount):
		data = struct.unpack("<ffffffffffffH", f.read(50))
		m._addFace(data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11])

def loadScene(filename):
	obj = mesh.printableObject(os.path.basename(filename))
	m = obj._addMesh()

	f = open(filename, "rb")
	if f.read(5).lower() == "solid":
		_loadAscii(m, f)
		if m.vertexCount < 3:
			f.seek(5, os.SEEK_SET)
			_loadBinary(m, f)
	else:
		_loadBinary(m, f)
	f.close()
	obj._postProcessAfterLoad()
	return [obj]

def saveScene(filename, objects):
	f = open(filename, 'wb')
	#Write the STL binary header. This can contain any info, except for "SOLID" at the start.
	f.write(("CURA BINARY STL EXPORT. " + time.strftime('%a %d %b %Y %H:%M:%S')).ljust(80, '\000'))

	vertexCount = 0
	for obj in objects:
		for m in obj._meshList:
			vertexCount += m.vertexCount

	#Next follow 4 binary bytes containing the amount of faces, and then the face information.
	f.write(struct.pack("<I", int(vertexCount / 3)))
	for obj in objects:
		for m in obj._meshList:
			vertexes = m.getTransformedVertexes(True)
			for idx in xrange(0, m.vertexCount, 3):
				v1 = vertexes[idx]
				v2 = vertexes[idx+1]
				v3 = vertexes[idx+2]
				f.write(struct.pack("<fff", 0.0, 0.0, 0.0))
				f.write(struct.pack("<fff", v1[0], v1[1], v1[2]))
				f.write(struct.pack("<fff", v2[0], v2[1], v2[2]))
				f.write(struct.pack("<fff", v3[0], v3[1], v3[2]))
				f.write(struct.pack("<H", 0))
	f.close()
