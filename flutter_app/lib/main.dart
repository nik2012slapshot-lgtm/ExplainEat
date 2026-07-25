import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

void main() {
  runApp(const ExplainEatApp());
}

class ExplainEatApp extends StatelessWidget {
  const ExplainEatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ExplainEat',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const ExplainEatHome(),
    );
  }
}

class ExplainEatHome extends StatefulWidget {
  const ExplainEatHome({super.key});

  @override
  State<ExplainEatHome> createState() => _ExplainEatHomeState();
}

class _ExplainEatHomeState extends State<ExplainEatHome> {
    final _backendUrlController =
      TextEditingController(text: kIsWeb ? 'http://127.0.0.1:5000' : 'http://10.0.2.2:5000');
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _ageController = TextEditingController(text: '30');
  final _weightController = TextEditingController(text: '70');
  final _activityController = TextEditingController(text: 'moderate');
  final _goalController = TextEditingController(text: 'health');
  final _allergiesController = TextEditingController();
  final _foodItemsController = TextEditingController();
  final List<Map<String, String>> _manualFoodItems = [
    {'name': '', 'grams': ''},
  ];

  // Quick nutrition database (per 100g)
  static final Map<String, Map<String, dynamic>> _nutritionData = {
    'rice': {'calories': 130, 'protein': 2.7, 'fat': 0.3, 'carbs': 28.0, 'fiber': 0.4},
    'chicken': {'calories': 165, 'protein': 31.0, 'fat': 3.6, 'carbs': 0.0, 'fiber': 0.0},
    'beef': {'calories': 250, 'protein': 26.0, 'fat': 17.0, 'carbs': 0.0, 'fiber': 0.0},
    'potatoes': {'calories': 77, 'protein': 2.0, 'fat': 0.1, 'carbs': 17.0, 'fiber': 2.2},
    'cucumber': {'calories': 16, 'protein': 0.7, 'fat': 0.1, 'carbs': 3.6, 'fiber': 0.5},
    'apple': {'calories': 52, 'protein': 0.3, 'fat': 0.2, 'carbs': 14.0, 'fiber': 2.4},
    'banana': {'calories': 89, 'protein': 1.1, 'fat': 0.3, 'carbs': 23.0, 'fiber': 2.6},
    'bread': {'calories': 265, 'protein': 9.0, 'fat': 3.2, 'carbs': 49.0, 'fiber': 2.7},
    'salad': {'calories': 15, 'protein': 1.0, 'fat': 0.2, 'carbs': 2.9, 'fiber': 1.4},
    'tomato': {'calories': 18, 'protein': 0.9, 'fat': 0.2, 'carbs': 3.9, 'fiber': 1.2},
  };

  // Quickly compute nutrition for a food item
  Map<String, dynamic> _getQuickNutrition(String name, int grams) {
    if (grams <= 0) return {};
    final data = _nutritionData[name.toLowerCase()];
    if (data == null) return {};
    final factor = grams / 100.0;
    return {
      'calories': ((data['calories'] as num) * factor).toStringAsFixed(0),
      'protein': ((data['protein'] as num) * factor).toStringAsFixed(1),
      'carbs': ((data['carbs'] as num) * factor).toStringAsFixed(1),
    };
  }


  bool _authenticated = false;
  bool _isRegisterMode = false;
  bool _isLoading = false;
  bool _analysisReady = false;
  String _statusMessage = 'Please log in or register.';
  String _selectedMode = 'Phone';
  String _currentUser = '';

  Uint8List? _pickedImageBytes;
  List<Map<String, dynamic>> _detectedItems = [];
  Map<String, dynamic>? _nutritionReport;
  List<String> _explanations = [];
  List<String> _shoppingList = [];
  bool _aiPowered = false;
  List<Map<String, dynamic>> _recipes = [];
  List<Map<String, dynamic>> _suggestions = [];
  bool _aiEnabled = false;
  String? _selectedRecipeId;
  Map<String, dynamic>? _recipeShopping;
  String? _recipeAdvice;
  List<Map<String, dynamic>> _plannedMeals = [];
  final _mealDateController = TextEditingController();
  final _mealTimeController = TextEditingController();
  final _mealNotesController = TextEditingController();

  Uri get _backendUri => Uri.parse(_backendUrlController.text.trim());

  Future<void> _setLoading(bool value) async {
    if (!mounted) return;
    setState(() {
      _isLoading = value;
    });
  }

  Future<void> _showMessage(String message) async {
    if (!mounted) return;
    setState(() {
      _statusMessage = message;
    });
  }

  Future<Map<String, dynamic>> _postJson(
      String path, Map<String, dynamic> body) async {
    final uri = _backendUri.replace(path: path);
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _getJson(String path) async {
    final uri = _backendUri.replace(path: path);
    final response = await http.get(uri);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> _loadPlannedMeals() async {
    try {
      final result = await _getJson('/meals?username=${Uri.encodeComponent(_currentUser)}');
      if (result['success'] == true) {
        final meals = (result['meals'] as List<dynamic>?)
                ?.map((e) => Map<String, dynamic>.from(e as Map<dynamic, dynamic>))
                .toList() ??
            [];
        setState(() {
          _plannedMeals = meals;
        });
      }
    } catch (_) {
      // ignore if the calendar is not available yet
    }
  }

  Future<void> _loadRecipes() async {
    try {
      final result = await _getJson('/recipes');
      if (result['success'] == true) {
        final recipes = (result['recipes'] as List<dynamic>?)
                ?.map((e) => Map<String, dynamic>.from(e as Map<dynamic, dynamic>))
                .toList() ??
            [];
        setState(() {
          _recipes = recipes;
          _aiEnabled = result['ai_enabled'] == true;
        });
      }
    } catch (_) {
      // ignore if recipes are not available yet
    }
  }

  Future<void> _selectRecipe(String recipeId) async {
    await _setLoading(true);
    setState(() {
      _selectedRecipeId = recipeId;
      _recipeShopping = null;
      _recipeAdvice = null;
    });
    try {
      final result = await _postJson('/recipes/shopping', {
        'recipe_id': recipeId,
        'age': int.tryParse(_ageController.text.trim()) ?? 30,
        'weight': double.tryParse(_weightController.text.trim()) ?? 70.0,
        'activity': _activityController.text.trim(),
        'goal': _goalController.text.trim(),
        'allergies': _allergiesController.text.trim(),
      });
      if (result['success'] == true) {
        setState(() {
          _recipeShopping = Map<String, dynamic>.from(result['shopping_list'] as Map);
          _recipeAdvice = result['advice']?.toString();
        });
        await _setLoading(false);
        _showRecipeResultSheet();
        return;
      } else {
        await _showMessage(result['message']?.toString() ?? 'Could not build shopping list.');
      }
    } catch (e) {
      await _showMessage('Could not build shopping list: $e');
    } finally {
      await _setLoading(false);
    }
  }

  void _showRecipeResultSheet() {
    if (!mounted || _recipeShopping == null) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.75,
        minChildSize: 0.4,
        maxChildSize: 0.95,
        builder: (ctx, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          child: _buildRecipeShoppingResult(),
        ),
      ),
    );
  }

  Future<void> _loadSuggestions() async {
    try {
      final result = await _postJson('/recipes/suggest', {
        'age': int.tryParse(_ageController.text.trim()) ?? 30,
        'weight': double.tryParse(_weightController.text.trim()) ?? 70.0,
        'activity': _activityController.text.trim(),
        'goal': _goalController.text.trim(),
        'allergies': _allergiesController.text.trim(),
        'limit': 10,
      });
      if (result['success'] == true) {
        final s = (result['suggestions'] as List<dynamic>?)
                ?.map((e) => Map<String, dynamic>.from(e as Map<dynamic, dynamic>))
                .toList() ??
            [];
        setState(() {
          _suggestions = s;
        });
      }
    } catch (_) {
      // ignore if suggestions are not available
    }
  }

  Future<void> _generateRecipe() async {
    await _setLoading(true);
    setState(() {
      _selectedRecipeId = null;
      _recipeShopping = null;
      _recipeAdvice = null;
    });
    try {
      final result = await _postJson('/recipes/generate', {
        'age': int.tryParse(_ageController.text.trim()) ?? 30,
        'weight': double.tryParse(_weightController.text.trim()) ?? 70.0,
        'activity': _activityController.text.trim(),
        'goal': _goalController.text.trim(),
        'allergies': _allergiesController.text.trim(),
      });
      if (result['success'] == true) {
        setState(() {
          _recipeShopping = Map<String, dynamic>.from(result['shopping_list'] as Map);
          _recipeAdvice = result['advice']?.toString();
        });
        await _setLoading(false);
        await _showMessage('The AI created a recipe just for you.');
        _showRecipeResultSheet();
        return;
      } else {
        await _showMessage(result['message']?.toString() ?? 'Could not generate a recipe.');
      }
    } catch (e) {
      await _showMessage('Could not generate a recipe: $e');
    } finally {
      await _setLoading(false);
    }
  }

  Future<void> _savePlannedMeal() async {
    if (_currentUser.isEmpty) {
      await _showMessage('Please log in first.');
      return;
    }

    if (_mealDateController.text.isEmpty || _mealTimeController.text.isEmpty) {
      await _showMessage('Date and time are required.');
      return;
    }

    await _setLoading(true);
    try {
      final result = await _postJson('/meals', {
        'username': _currentUser,
        'date': _mealDateController.text.trim(),
        'time': _mealTimeController.text.trim(),
        'items': _foodItemsController.text.trim().split('\n'),
        'notes': _mealNotesController.text.trim(),
      });
      if (result['success'] == true) {
        await _showMessage('Meal saved.');
        _mealNotesController.clear();
        await _loadPlannedMeals();
      } else {
        await _showMessage(result['message']?.toString() ?? 'Saving failed.');
      }
    } catch (e) {
      await _showMessage('Saving failed: $e');
    } finally {
      await _setLoading(false);
    }
  }

  void _addManualFoodItem() {
    setState(() {
      _manualFoodItems.add({'name': '', 'grams': ''});
    });
  }

  void _removeManualFoodItem(int index) {
    setState(() {
      if (_manualFoodItems.length > 1) {
        _manualFoodItems.removeAt(index);
      } else {
        _manualFoodItems[0] = {'name': '', 'grams': ''};
      }
    });
  }

  Future<void> _deletePlannedMeal(String mealId) async {
    await _setLoading(true);
    try {
      final uri = _backendUri.replace(path: '/meals/$mealId');
      final response = await http.delete(uri);
      final result = jsonDecode(response.body) as Map<String, dynamic>;
      if (result['success'] == true) {
        await _showMessage('Meal deleted.');
        await _loadPlannedMeals();
      } else {
        await _showMessage(result['message']?.toString() ?? 'Deleting failed.');
      }
    } catch (e) {
      await _showMessage('Deleting failed: $e');
    } finally {
      await _setLoading(false);
    }
  }

  Future<void> _retrainModel() async {
    await _setLoading(true);
    try {
      final result = await _postJson('/training/retrain', {
        'epochs': 8,
        'batch_size': 24,
        'img_size': 224,
        'val_split': 0.15,
        'device': 'cpu',
      });
      await _showMessage(result['message']?.toString() ?? 'Retraining started.');
    } catch (e) {
      await _showMessage('Retraining failed: $e');
    } finally {
      await _setLoading(false);
    }
  }

  Future<void> _pickDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date != null) {
      setState(() {
        _mealDateController.text = date.toIso8601String().split('T').first;
      });
    }
  }

  Future<void> _pickTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (time != null) {
      setState(() {
        _mealTimeController.text = time.format(context);
      });
    }
  }

  Future<void> _login() async {
    await _setLoading(true);
    try {
      final result = await _postJson('/login', {
        'username': _usernameController.text.trim(),
        'password': _passwordController.text.trim(),
      });
      if (result['success'] == true) {
        final profile = result['profile'] as Map<String, dynamic>?;
        if (profile != null) {
          _ageController.text = profile['age']?.toString() ?? _ageController.text;
          _weightController.text = profile['weight']?.toString() ?? _weightController.text;
          _activityController.text = profile['activity_level']?.toString() ?? _activityController.text;
          _goalController.text = profile['goal']?.toString() ?? _goalController.text;
          _allergiesController.text = (profile['allergies'] as List<dynamic>?)?.join(', ') ?? _allergiesController.text;
        }
        setState(() {
          _authenticated = true;
          _currentUser = _usernameController.text.trim();
        });
        await _loadPlannedMeals();
        await _loadRecipes();
        await _loadSuggestions();
        await _showMessage('Login successful.');
      } else {
        await _showMessage(result['message'] ?? 'Login failed.');
      }
    } catch (e) {
      await _showMessage('Server not reachable. Check the backend URL.');
    } finally {
      await _setLoading(false);
    }
  }

  Future<void> _register() async {
    if (_usernameController.text.trim().isEmpty || _passwordController.text.trim().isEmpty || _ageController.text.trim().isEmpty || _weightController.text.trim().isEmpty || _activityController.text.trim().isEmpty || _goalController.text.trim().isEmpty) {
      await _showMessage('Please fill in all registration fields.');
      return;
    }
    await _setLoading(true);
    try {
      final result = await _postJson('/register', {
        'username': _usernameController.text.trim(),
        'password': _passwordController.text.trim(),
        'age': int.tryParse(_ageController.text.trim()) ?? 30,
        'weight': double.tryParse(_weightController.text.trim()) ?? 70.0,
        'activity': _activityController.text.trim(),
        'goal': _goalController.text.trim(),
        'allergies': _allergiesController.text.trim(),
      });
      if (result['success'] == true) {
        setState(() {
          _authenticated = true;
          _currentUser = _usernameController.text.trim();
        });
        await _loadPlannedMeals();
        await _loadRecipes();
        await _loadSuggestions();
      }
      await _showMessage(result['message'] ?? 'Registration complete.');
    } catch (e) {
      await _showMessage('Registration failed. Check backend or inputs.');
    } finally {
      await _setLoading(false);
    }
  }

  Future<void> _analyze() async {
    final foodItems = _manualFoodItems
        .where((item) => (item['name']?.trim().isNotEmpty ?? false))
        .map((item) => {
              'name': item['name']?.trim() ?? '',
              'grams': int.tryParse(item['grams']?.trim() ?? '') ?? 0,
            })
        .toList();

    await _setLoading(true);
    try {
      final result = await _postJson('/analyze', {
        'age': int.tryParse(_ageController.text.trim()) ?? 30,
        'weight': double.tryParse(_weightController.text.trim()) ?? 70.0,
        'activity': _activityController.text.trim(),
        'goal': _goalController.text.trim(),
        'allergies': _allergiesController.text.trim(),
        'food_items': foodItems,
      });
      _displayResult(result);
    } catch (e) {
      await _showMessage('Analysis failed: $e');
    } finally {
      await _setLoading(false);
    }
  }

  Future<void> _analyzeImage(ImageSource source) async {
    final picker = ImagePicker();
    final image = await picker.pickImage(source: source, imageQuality: 85);
    if (image == null) {
      await _showMessage('Image selection cancelled.');
      return;
    }
    final bytes = await image.readAsBytes();
    setState(() {
      _pickedImageBytes = bytes;
    });

    await _setLoading(true);
    try {
      final uri = _backendUri.replace(path: '/analyze_image');
      final request = http.MultipartRequest('POST', uri);
      request.fields.addAll({
        'age': _ageController.text.trim(),
        'weight': _weightController.text.trim(),
        'activity': _activityController.text.trim(),
        'goal': _goalController.text.trim(),
        'allergies': _allergiesController.text.trim(),
      });
      if (kIsWeb) {
        request.files.add(http.MultipartFile.fromBytes(
          'image',
          bytes,
          filename: image.name.isNotEmpty ? image.name : 'upload.jpg',
        ));
      } else {
        request.files.add(await http.MultipartFile.fromPath('image', image.path));
      }
      final streamed = await request.send();
      final responseBody = await streamed.stream.bytesToString();
      final result = jsonDecode(responseBody) as Map<String, dynamic>;
      _displayResult(result);
    } catch (e) {
      await _showMessage('Image analysis failed: $e');
    } finally {
      await _setLoading(false);
    }
  }

  void _displayResult(Map<String, dynamic> result) {
    if (result['success'] != true) {
      _showMessage(result['message']?.toString() ?? 'Error during analysis.');
      return;
    }

    final items = (result['detected_items'] as List<dynamic>?)
            ?.map((e) => Map<String, dynamic>.from(e as Map<dynamic, dynamic>))
            .toList() ??
        [];
    final nutrition = result['nutrition_report'] as Map<String, dynamic>?;
    final explanations = (result['explanations'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];
    final shopping = (result['shopping_recommendations'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];

    setState(() {
      _analysisReady = true;
      _detectedItems = items;
      _nutritionReport = nutrition;
      _explanations = explanations;
      _shoppingList = shopping;
      _aiPowered = result['ai_powered'] == true;
      _statusMessage = 'Analysis completed successfully.';
    });
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: _authenticated ? Scaffold(
        appBar: AppBar(
          title: const Text('ExplainEat'),
          elevation: 0,
          centerTitle: true,
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.restaurant_menu), text: 'Analyze'),
              Tab(icon: Icon(Icons.shopping_cart), text: 'Shopping'),
              Tab(icon: Icon(Icons.lightbulb), text: 'Recommendations'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildAnalyzeTab(context),
            _buildShoppingTab(),
            _buildRecommendationsTab(),
          ],
        ),
      ) : _buildAuthScreen(),
    );
  }

  Widget _buildAuthScreen() {
    return Scaffold(
      appBar: AppBar(title: const Text('ExplainEat Login')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 24),
            const Text('Welcome to ExplainEat',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Log in or register to save your own nutrition data.'),
            const SizedBox(height: 20),
            TextField(
              controller: _backendUrlController,
              decoration: const InputDecoration(labelText: 'Backend URL'),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: FilledButton(
                    onPressed: _isLoading ? null : () {
                      setState(() {
                        _isRegisterMode = false;
                      });
                    },
                    child: const Text('Login'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: _isLoading ? null : () {
                      setState(() {
                        _isRegisterMode = true;
                      });
                    },
                    child: const Text('Register'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_isRegisterMode) ...[
              TextField(
                controller: _ageController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Age'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _weightController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Weight (kg)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _activityController,
                decoration: const InputDecoration(labelText: 'Activity (low/moderate/high)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _goalController,
                decoration: const InputDecoration(labelText: 'Goal (health/muscle/weight_loss)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _allergiesController,
                decoration: const InputDecoration(labelText: 'Allergies (comma-separated)'),
              ),
              const SizedBox(height: 20),
            ],
            TextField(
              controller: _usernameController,
              decoration: const InputDecoration(labelText: 'Username'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Password'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _isLoading ? null : (_isRegisterMode ? _register : _login),
              child: Text(_isRegisterMode ? 'Register' : 'Login'),
            ),
            const SizedBox(height: 16),
            if (_isLoading) const LinearProgressIndicator(),
            const SizedBox(height: 16),
            Text(_statusMessage, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            if (_authenticated)
              FilledButton.tonal(
                onPressed: () {
                  setState(() {
                    _authenticated = false;
                    _currentUser = '';
                  });
                },
                child: const Text('Log out'),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildWelcomeCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome, $_currentUser',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            const Text('Here you can analyze your meals and improve your nutrition.'),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalyzeTab(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 450),
      child: ListView(
        key: const ValueKey('analyzeTab'),
        padding: const EdgeInsets.all(16),
        children: [
          _buildHeaderCard(),
          const SizedBox(height: 16),
          _buildWelcomeCard(),
          const SizedBox(height: 16),
          _buildProfileCard(),
          const SizedBox(height: 16),
          _buildImageCard(context),
          const SizedBox(height: 16),
          _buildManualInputCard(),
          const SizedBox(height: 16),
          _buildActionButtons(),
          const SizedBox(height: 16),
          if (_isLoading) const LinearProgressIndicator(),
          const SizedBox(height: 12),
          _buildStatusChip(),
          const SizedBox(height: 16),
          _analysisReady ? _buildResultOverview() : _buildPlaceholderCard(),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildAiBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.deepPurple.shade50,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.deepPurple.shade100),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_awesome, size: 14, color: Colors.deepPurple.shade400),
          const SizedBox(width: 4),
          Text('AI powered',
              style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.deepPurple.shade400)),
        ],
      ),
    );
  }

  // Allergen categories -> keywords that reveal a hidden allergen
  // (mirrors explain_eat/allergens.py so the UI hides the same recipes).
  static const Map<String, List<String>> _allergenKeywords = {
    'nuts': ['nut', 'nuts', 'peanut', 'peanuts', 'almond', 'almonds', 'cashew',
             'walnut', 'walnuts', 'hazelnut', 'pecan', 'pistachio', 'pesto', 'marzipan', 'nutella'],
    'dairy': ['milk', 'cheese', 'yogurt', 'yoghurt', 'butter', 'cream', 'tzatziki',
              'mozzarella', 'parmesan', 'feta', 'dairy', 'cheddar'],
    'egg': ['egg', 'eggs', 'mayonnaise', 'mayo', 'aioli', 'omelette', 'omelet'],
    'gluten': ['gluten', 'wheat', 'bread', 'breadcrumbs', 'pasta', 'noodle', 'noodles',
               'couscous', 'flour', 'barley', 'rye', 'bulgur', 'spaghetti'],
    'fish': ['fish', 'salmon', 'tuna', 'cod', 'mackerel', 'sardine', 'anchovy', 'trout'],
    'shellfish': ['shrimp', 'prawn', 'crab', 'lobster', 'shellfish', 'scampi',
                  'crayfish', 'clam', 'mussel', 'oyster', 'squid', 'calamari'],
    'soy': ['soy', 'soya', 'tofu', 'edamame', 'tempeh', 'miso'],
    'sesame': ['sesame', 'tahini'],
  };
  static const Map<String, String> _allergySynonyms = {
    'nut': 'nuts', 'nuts': 'nuts', 'peanut': 'nuts', 'nuss': 'nuts', 'nüsse': 'nuts',
    'milk': 'dairy', 'dairy': 'dairy', 'lactose': 'dairy', 'milch': 'dairy', 'laktose': 'dairy',
    'egg': 'egg', 'eggs': 'egg', 'ei': 'egg', 'eier': 'egg',
    'gluten': 'gluten', 'wheat': 'gluten', 'weizen': 'gluten',
    'fish': 'fish', 'fisch': 'fish',
    'shellfish': 'shellfish', 'seafood': 'shellfish', 'meeresfrüchte': 'shellfish', 'schalentiere': 'shellfish',
    'soy': 'soy', 'soya': 'soy', 'soja': 'soy',
    'sesame': 'sesame', 'sesam': 'sesame',
  };

  List<String> _userAllergies() => _allergiesController.text
      .split(',')
      .map((e) => e.trim().toLowerCase())
      .where((e) => e.isNotEmpty)
      .toList();

  bool _wordMatch(String text, String word) =>
      RegExp('\\b${RegExp.escape(word)}\\b').hasMatch(text);

  bool _ingredientConflicts(String name, List<String> terms) {
    if (terms.isEmpty) return false;
    final n = name.toLowerCase();
    if (terms.any((t) => _wordMatch(n, t))) return true;
    final cats = <String>{};
    for (final t in terms) {
      final c = _allergySynonyms[t] ?? (_allergenKeywords.containsKey(t) ? t : null);
      if (c != null) cats.add(c);
    }
    if (cats.isEmpty) return false;
    final ingCats = <String>{};
    _allergenKeywords.forEach((cat, kws) {
      if (kws.any((k) => _wordMatch(n, k))) ingCats.add(cat);
    });
    return ingCats.intersection(cats).isNotEmpty;
  }

  bool _recipeHasAllergen(Map<String, dynamic> recipe, List<String> allergens) {
    if (allergens.isEmpty) return false;
    final ingredients = (recipe['ingredients'] as List<dynamic>?) ?? [];
    for (final i in ingredients) {
      final name = (i is Map && i['name'] != null) ? i['name'].toString() : '';
      if (_ingredientConflicts(name, allergens)) return true;
    }
    return false;
  }

  List<Widget> _buildRecipeList() {
    final widgets = <Widget>[];
    if (_recipes.isEmpty) {
      widgets.add(const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('No recipes available yet. Add your own in explain_eat/recipes.json.'),
        ),
      ));
      return widgets;
    }
    final allergens = _userAllergies();
    final visible = _recipes.where((r) => !_recipeHasAllergen(r, allergens)).toList();
    final hidden = _recipes.length - visible.length;

    if (visible.isEmpty) {
      widgets.add(const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text(
              "Every recipe contains an ingredient you don't tolerate. Use \"Generate a recipe for me\" above — the AI builds one around your allergies."),
        ),
      ));
    }
    widgets.addAll(visible.map(_buildRecipeCard));
    if (hidden > 0) {
      widgets.add(Padding(
        padding: const EdgeInsets.only(top: 8, bottom: 4),
        child: Row(
          children: [
            Icon(Icons.shield_outlined, size: 14, color: Colors.grey.shade600),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                "$hidden recipe(s) hidden because they contain ingredients you don't tolerate.",
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
              ),
            ),
          ],
        ),
      ));
    }
    return widgets;
  }

  Widget _buildShoppingTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            const Text('Recipes',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const Spacer(),
            if (_aiEnabled) _buildAiBadge(),
          ],
        ),
        const SizedBox(height: 6),
        const Text(
            'Pick a recipe and the AI builds a shopping list scaled to your body weight, activity and goal — or let the AI invent one for you.'),
        const SizedBox(height: 12),
        FilledButton.icon(
          icon: const Icon(Icons.auto_awesome),
          label: const Text('Generate a recipe for me'),
          style: FilledButton.styleFrom(backgroundColor: Colors.deepPurple),
          onPressed: _isLoading ? null : _generateRecipe,
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            const Text('Recommended for you',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(width: 8),
            if (_aiEnabled) _buildAiBadge(),
            const Spacer(),
            IconButton(
              tooltip: 'Refresh suggestions',
              icon: const Icon(Icons.refresh, size: 20),
              onPressed: _isLoading ? null : _loadSuggestions,
            ),
          ],
        ),
        const Text('The AI ranked these to fit your body weight, goal and allergies.',
            style: TextStyle(fontSize: 13, color: Colors.grey)),
        const SizedBox(height: 8),
        if (_suggestions.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Text('Tap the refresh icon to get personalized suggestions.'),
          )
        else
          ..._suggestions.map(_buildRecipeCard),
        const SizedBox(height: 20),
        const Text('All recipes',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ..._buildRecipeList(),
        const SizedBox(height: 24),
        const Text('Tips from your last analysis',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (_shoppingList.isEmpty)
          const Text('No recommendations yet. Run an analysis first.')
        else
          ..._shoppingList.map((rec) => Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: ListTile(
                  leading: const Icon(Icons.local_grocery_store,
                      color: Colors.green),
                  title: Text(rec),
                ),
              )),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildRecipeCard(Map<String, dynamic> recipe) {
    final id = recipe['id']?.toString() ?? '';
    final selected = id == _selectedRecipeId;
    final tags = (recipe['tags'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: selected
            ? const BorderSide(color: Colors.green, width: 2)
            : BorderSide.none,
      ),
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(recipe['name']?.toString() ?? 'Recipe',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
                if (recipe['score'] != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.green.shade50,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.green.shade200),
                    ),
                    child: Text('${recipe['score']}/100',
                        style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Colors.green.shade700)),
                  ),
              ],
            ),
            if ((recipe['description']?.toString() ?? '').isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(recipe['description'].toString()),
            ],
            if (tags.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                children: tags
                    .map((t) => Chip(
                          label: Text(t, style: const TextStyle(fontSize: 11)),
                          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: FilledButton.icon(
                icon: const Icon(Icons.shopping_cart_checkout, size: 18),
                label: Text(selected ? 'Update shopping list' : 'Get shopping list'),
                onPressed: _isLoading ? null : () => _selectRecipe(id),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecipeShoppingResult() {
    final shopping = _recipeShopping!;
    final items = (shopping['items'] as List<dynamic>?)
            ?.map((e) => Map<String, dynamic>.from(e as Map))
            .toList() ??
        [];
    final scale = shopping['scale_factor'];
    final steps = (shopping['steps'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                      'Shopping list — ${shopping['recipe_name'] ?? ''}',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                Chip(
                  label: Text('×$scale', style: const TextStyle(fontSize: 12)),
                  backgroundColor: Colors.green.shade50,
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text('Portions scaled to your body weight, activity and goal.',
                style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
            const SizedBox(height: 12),
            ...items.map((it) {
              final warn = it['allergy_warning'] == true;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Icon(warn ? Icons.warning_amber : Icons.check_circle_outline,
                        size: 18, color: warn ? Colors.orange : Colors.green),
                    const SizedBox(width: 8),
                    Expanded(child: Text(it['name']?.toString() ?? '')),
                    Text('${it['grams']} g',
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                  ],
                ),
              );
            }),
            if (_recipeAdvice != null && _recipeAdvice!.isNotEmpty) ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.deepPurple.shade50,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.auto_awesome,
                            size: 16, color: Colors.deepPurple.shade400),
                        const SizedBox(width: 6),
                        Text('AI advice',
                            style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.deepPurple.shade400)),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(_recipeAdvice!),
                  ],
                ),
              ),
            ],
            if (steps.isNotEmpty) ...[
              const SizedBox(height: 14),
              const Text('Preparation',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              ...steps.asMap().entries.map((e) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text('${e.key + 1}. ${e.value}'),
                  )),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendationsTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Recommendations',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Expanded(
            child: _analysisReady
                ? ListView(
                    children: [
                      if (_nutritionReport != null)
                        _buildNutritionSummaryCard(),
                      const SizedBox(height: 12),
                      _buildExplanationCard(),
                    ],
                  )
                : const Center(
                    child: Text(
                        'Start an analysis to get personalized recommendations.')),
          ),
        ],
      ),
    );
  }

  Widget _buildCalendarTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Calendar',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('Add a planned meal',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _mealDateController,
                    readOnly: true,
                    decoration: const InputDecoration(labelText: 'Date'),
                    onTap: _pickDate,
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _mealTimeController,
                    readOnly: true,
                    decoration: const InputDecoration(labelText: 'Time'),
                    onTap: _pickTime,
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _mealNotesController,
                    decoration: const InputDecoration(labelText: 'Note / ingredients'),
                    maxLines: 3,
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _isLoading ? null : _savePlannedMeal,
                    child: const Text('Schedule meal'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: _plannedMeals.isEmpty
                ? const Center(child: Text('No planned meals yet.'))
                : ListView.builder(
                    itemCount: _plannedMeals.length,
                    itemBuilder: (context, index) {
                      final meal = _plannedMeals[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 6),
                        child: ListTile(
                          title: Text('${meal['date']} ${meal['time']}'),
                          subtitle: Text((meal['items'] as List<dynamic>?)?.join(', ') ?? meal['notes'] ?? ''),
                          trailing: IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _deletePlannedMeal(meal['id'].toString()),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: ListView(
        children: [
          const Text('Settings',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildSettingsCard(),
          const SizedBox(height: 16),
          _buildTrainingCard(),
          const SizedBox(height: 16),
          _buildBackendCard(),
          const SizedBox(height: 16),
          Card(
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text('ExplainEat Mobile',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  Text(
                      'This app connects to your local ExplainEat backend and analyzes nutrition with AI. Here you can manage your settings, backend URL and login details.'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderCard() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 500),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
            colors: [Color(0xFF0F9D58), Color(0xFF34A853)]),
        borderRadius: BorderRadius.circular(24),
        boxShadow: const [
          BoxShadow(color: Colors.black12, blurRadius: 18, offset: Offset(0, 8))
        ],
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          Text('ExplainEat',
              style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.white)),
          SizedBox(height: 8),
          Text(
              'Track your meals, upload photos and get personalized shopping tips and recommendations.',
              style: TextStyle(color: Colors.white70, height: 1.4)),
        ],
      ),
    );
  }

  Widget _buildProfileCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('User profile',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            TextField(
                controller: _ageController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Age')),
            const SizedBox(height: 10),
            TextField(
                controller: _weightController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Weight (kg)')),
            const SizedBox(height: 10),
            TextField(
                controller: _activityController,
                decoration: const InputDecoration(
                    labelText: 'Activity (low/moderate/high)')),
            const SizedBox(height: 10),
            TextField(
                controller: _goalController,
                decoration: const InputDecoration(
                    labelText: 'Goal (health/muscle/weight_loss)')),
            const SizedBox(height: 10),
            TextField(
                controller: _allergiesController,
                decoration: const InputDecoration(
                    labelText: 'Allergies (comma-separated)')),
          ],
        ),
      ),
    );
  }

  Widget _buildImageCard(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Photo & upload',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 400),
              child: _pickedImageBytes == null
                  ? SizedBox(
                      height: 170,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Center(
                            child: Icon(Icons.camera_alt_outlined,
                                size: 48, color: Colors.green)),
                      ),
                    )
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Image.memory(_pickedImageBytes!,
                          height: 170, fit: BoxFit.cover),
                    ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                ElevatedButton.icon(
                  icon: const Icon(Icons.photo_camera),
                  label: const Text('Take photo'),
                  onPressed: _isLoading
                      ? null
                      : () => _analyzeImage(ImageSource.camera),
                ),
                ElevatedButton.icon(
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Choose from gallery'),
                  onPressed: _isLoading
                      ? null
                      : () => _analyzeImage(ImageSource.gallery),
                ),
              ],
            ),
            const SizedBox(height: 10),
            const Text(
                'Upload or take a photo directly in the app to analyze your meal with AI.'),
          ],
        ),
      ),
    );
  }

  Widget _buildManualInputCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Manual input',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            const Text(
              'Enter the name and amount in grams for each food. The nutrition values are shown instantly.',
            ),
            const SizedBox(height: 12),
            ..._manualFoodItems.asMap().entries.map((entry) {
              final index = entry.key;
              final item = entry.value;
              final name = item['name']?.trim() ?? '';
              final grams = int.tryParse(item['grams']?.trim() ?? '') ?? 0;
              final nutrition = _getQuickNutrition(name, grams);

              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          flex: 5,
                          child: TextField(
                            key: ValueKey('name-$index'),
                            decoration: const InputDecoration(
                              labelText: 'Food',
                              hintText: 'e.g. rice',
                            ),
                            onChanged: (value) {
                              item['name'] = value;
                              setState(() {});
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 2,
                          child: TextField(
                            key: ValueKey('grams-$index'),
                            decoration: const InputDecoration(
                              labelText: 'Grams',
                              hintText: '100',
                            ),
                            keyboardType: TextInputType.number,
                            onChanged: (value) {
                              item['grams'] = value;
                              setState(() {});
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        IconButton(
                          icon: const Icon(Icons.delete, color: Colors.red),
                          onPressed: () => _removeManualFoodItem(index),
                        ),
                      ],
                    ),
                    if (nutrition.isNotEmpty && grams > 0) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.green.shade200),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              '${nutrition['calories']} kcal',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                            Text(
                              'Protein: ${nutrition['protein']}g',
                              style: const TextStyle(fontSize: 12),
                            ),
                            Text(
                              'Carbs: ${nutrition['carbs']}g',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ] else if (name.isNotEmpty && grams <= 0) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Please enter grams',
                        style: TextStyle(fontSize: 12, color: Colors.orange.shade700),
                      ),
                    ],
                  ],
                ),
              );
            }).toList(),
            FilledButton.tonal(
              onPressed: _isLoading ? null : _addManualFoodItem,
              child: const Text('Add another ingredient'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
            child: FilledButton(
                onPressed: _isLoading ? null : _analyze,
                child: const Text('Manual analysis'))),
      ],
    );
  }

  Widget _buildStatusChip() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 400),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.green.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.green.shade100),
      ),
      child: Text(_statusMessage,
          style: const TextStyle(fontWeight: FontWeight.w500)),
    );
  }

  Widget _buildResultOverview() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          elevation: 2,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Quick overview',
                    style:
                        TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),
                AnimatedSize(
                  duration: const Duration(milliseconds: 400),
                  child: _detectedItems.isEmpty
                      ? const Text('No foods detected.')
                      : Wrap(
                          spacing: 10,
                          runSpacing: 10,
                          children: _detectedItems.map((item) {
                            return Chip(
                              avatar: const Icon(Icons.check_circle,
                                  color: Colors.green, size: 18),
                              label:
                                  Text('${item['name']} (${item['portion']})'),
                            );
                          }).toList(),
                        ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (_nutritionReport != null) _buildNutritionCard(),
      ],
    );
  }

  Widget _buildNutritionCard() {
    final macros = _nutritionReport!['macros'] as Map<String, dynamic>?;
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Nutrition',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            if (macros != null) ...[
              _buildKeyValue('Calories', '${macros['calories']} kcal'),
              _buildKeyValue('Protein', '${macros['protein_g']} g'),
              _buildKeyValue('Fat', '${macros['fat_g']} g'),
              _buildKeyValue('Carbohydrates', '${macros['carbs_g']} g'),
              _buildKeyValue('Fiber', '${macros['fiber_g']} g'),
              _buildKeyValue('Sugar', '${macros['sugar_g']} g'),
            ] else
              const Text('No nutrition data available.'),
          ],
        ),
      ),
    );
  }

  Widget _buildKeyValue(String key, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(key, style: const TextStyle(fontWeight: FontWeight.w600)),
          Text(value)
        ],
      ),
    );
  }

  Widget _buildPlaceholderCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Text('No analysis yet',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            Text(
                'Start in the Analyze tab with a photo or manual input to get recommendations and shopping tips.'),
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionSummaryCard() {
    final macros = _nutritionReport!['macros'] as Map<String, dynamic>?;
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Your profile',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            if (macros != null)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Calories: ${macros['calories']} kcal'),
                  Text('Protein: ${macros['protein_g']} g'),
                  Text('Fat: ${macros['fat_g']} g'),
                ],
              )
            else
              const Text('No nutrition data available yet.'),
          ],
        ),
      ),
    );
  }

  Widget _buildExplanationCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text('Explanations',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const Spacer(),
                if (_aiPowered) _buildAiBadge(),
              ],
            ),
            const SizedBox(height: 12),
            if (_explanations.isEmpty)
              const Text('No recommendations available.'),
            if (_explanations.isNotEmpty)
              ..._explanations.map(
                (text) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.arrow_right_rounded,
                          size: 20, color: Colors.green),
                      const SizedBox(width: 8),
                      Expanded(child: Text(text)),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingsCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Mode',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'Phone', label: Text('Phone')),
                ButtonSegment(value: 'Table', label: Text('Table')),
              ],
              selected: <String>{_selectedMode},
              onSelectionChanged: (selection) {
                setState(() {
                  _selectedMode = selection.first;
                });
              },
            ),
            const SizedBox(height: 14),
            const Text(
                'Choose the mode that best fits how you use the app.'),
          ],
        ),
      ),
    );
  }

  Widget _buildTrainingCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('AI training',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            const Text(
                'Here you can retrain the local classification model when new training images have been added.'),
            const SizedBox(height: 14),
            FilledButton.icon(
              icon: const Icon(Icons.auto_fix_high),
              label: const Text('Retrain model'),
              onPressed: _isLoading ? null : _retrainModel,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBackendCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Backend',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            TextField(
              controller: _backendUrlController,
              decoration: const InputDecoration(labelText: 'Backend URL'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Test backend'),
              onPressed: _isLoading
                  ? null
                  : () async {
                      await _setLoading(true);
                      try {
                        final response = await http
                            .get(_backendUri.replace(path: '/health'))
                            .timeout(const Duration(seconds: 5));
                        if (response.statusCode == 200) {
                          await _showMessage('Backend reachable.');
                        } else {
                          await _showMessage(
                              'Backend not responding correctly.');
                        }
                      } catch (_) {
                        await _showMessage('Backend not reachable.');
                      } finally {
                        await _setLoading(false);
                      }
                    },
            ),
          ],
        ),
      ),
    );
  }
}
