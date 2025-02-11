import 'dart:convert';
import 'dart:io';
import 'package:bloc/bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart';
import 'package:mime/mime.dart';

part 'file_upload_event.dart';
part 'file_upload_state.dart';

class FileUploadBloc extends Bloc<FileUploadEvent, FileUploadState> {
  FileUploadBloc() : super(FileUploadInitial());
  final String baseUrl = "http://localhost:3000/api/v1";

  Stream<FileUploadState> mapEventToState(FileUploadEvent event) async* {
    if (event is UploadFileEvent) {
      yield FileUploading();

      try {
        // Determine if it's an image or video
        final mimeType = lookupMimeType(event.file.path);
        final isImage = mimeType != null && mimeType.startsWith("image");

        final url = isImage ? "$baseUrl/image-analysis" : "$baseUrl/analyze";
        final request = http.MultipartRequest('POST', Uri.parse(url));

        // Add the file
        request.files.add(await http.MultipartFile.fromPath(
          'file',
          event.file.path,
          filename: basename(event.file.path),
        ));

        // Add additional fields if needed
        request.fields["prompt"] = event.prompt ?? "Analyze this file.";

        final streamedResponse = await request.send();
        final response = await http.Response.fromStream(streamedResponse);

        if (response.statusCode == 200) {
          final responseData = jsonDecode(response.body);
          yield FileUploadSuccess(file: event.file, response: responseData);
        } else {
          yield FileUploadFailure(error: "Server error: ${response.body}");
        }
      } catch (e) {
        yield FileUploadFailure(error: "Error uploading file: $e");
      }
    }
  }
}