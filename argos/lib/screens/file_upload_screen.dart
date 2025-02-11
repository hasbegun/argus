import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:file_picker/file_picker.dart';

import 'package:argos/bloc/file_upload_bloc.dart';
import 'package:argos/screens/constant.dart';

class FileUploadScreen extends StatelessWidget {
  const FileUploadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => FileUploadBloc(),
      child: Scaffold(
        appBar: AppBar(title: const Text("Upload Image or Video")),
        body: const FileUploadForm(),
      ),
    );
  }
}

class FileUploadForm extends StatefulWidget {
  const FileUploadForm({super.key});

  @override
  _FileUploadFormState createState() => _FileUploadFormState();
}

class _FileUploadFormState extends State<FileUploadForm> {
  File? _selectedFile;

  Future<void> _pickFile() async {
    // mobile works
    // final result = await FilePicker.platform.pickFiles(
    //   type: FileType.any,
    // );

    // new
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: allowedFileTypes,
    );
    /////

    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedFile = File(result.files.single.path!);
      });
    } else {
      // Show error if no file is selected
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("No file selected.")),
      );
    }
  }

  void _uploadFile(BuildContext context) {
    if (_selectedFile == null) return;

    BlocProvider.of<FileUploadBloc>(context)
        .add(UploadFileEvent(file: _selectedFile!));
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          if (_selectedFile != null) ...[
            Text("Selected file: ${_selectedFile!.path.split('/').last}"),
            SizedBox(height: 10),
          ],
          ElevatedButton(
            onPressed: _pickFile,
            child: const Text("Select Image or Video"),
          ),
          const SizedBox(height: 20),
          BlocConsumer<FileUploadBloc, FileUploadState>(
            listener: (context, state) {
              if (state is FileUploadFailure) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(state.error), backgroundColor: Colors.red),
                );
              }
            },
            builder: (context, state) {
              if (state is FileUploading) {
                return const CircularProgressIndicator();
              } else if (state is FileUploadSuccess) {
                return Column(
                  children: [
                    if (state.file.path.endsWith('.jpg') ||
                        state.file.path.endsWith('.png'))
                      Image.file(state.file, height: 200),
                    const SizedBox(height: 10),
                    const Text("Server Response:"),
                    Text(state.response.toString()),
                  ],
                );
              }
              return ElevatedButton(
                onPressed: () => _uploadFile(context),
                child: const Text("Upload"),
              );
            },
          ),
        ],
      ),
    );
  }
}